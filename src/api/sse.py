import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException, Request
from sse_starlette.sse import EventSourceResponse

from src.api.deps import get_current_user, get_db_cursor
from src.core.security import verify_company_access

router = APIRouter(prefix="/sse", tags=["sse"])


@router.get("/runs/{run_id}")
async def sse_run_stream(run_id: str, request: Request, user=Depends(get_current_user), cur=Depends(get_db_cursor)):
    # 1. Verify run ownership
    try:
        run_int_id = int(run_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Run tidak valid") from None

    cur.execute("SELECT company_id, shipment_id, status, outcome FROM agent_runs WHERE id = %s;", (run_int_id,))
    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Run tidak ditemukan")

    verify_company_access(int(row[0]), int(user["company_id"]))

    last_event_id = request.headers.get("Last-Event-ID", "0")
    try:
        last_seq = int(last_event_id)
    except ValueError:
        last_seq = 0

    async def event_generator():
        # Yield initial connected event
        yield {
            "event": "connected",
            "id": str(last_seq),
            "data": json.dumps({"run_id": run_id, "status": "connected"}),
        }

        # Poll database for new steps
        seen_seq = last_seq
        from src.core.config import settings
        import psycopg

        while True:
            if await request.is_disconnected():
                break

            try:
                with psycopg.connect(settings.DATABASE_URL) as stream_conn, stream_conn.cursor() as stream_cur:
                    stream_cur.execute("""
                        SELECT seq, step_name, tool_name, tool_output, step_outcome, created_at
                        FROM agent_steps
                        WHERE run_id = %s AND seq > %s
                        ORDER BY seq ASC;
                    """, (run_int_id, seen_seq))
                    new_steps = stream_cur.fetchall()

                    for step in new_steps:
                        seen_seq = step[0]
                        yield {
                            "event": "step",
                            "id": str(seen_seq),
                            "data": json.dumps({
                                "run_id": run_id,
                                "seq": step[0],
                                "step_name": step[1],
                                "tool_name": step[2],
                                "output": step[3],
                                "outcome": step[4],
                                "time": step[5].isoformat() if step[5] else None,
                            }, ensure_ascii=False),
                        }

                    stream_cur.execute("SELECT status, outcome FROM agent_runs WHERE id = %s;", (run_int_id,))
                    run_status = stream_cur.fetchone()
                    if run_status and run_status[0] in ("succeeded", "failed"):
                        yield {
                            "event": "end",
                            "id": str(seen_seq + 1),
                            "data": json.dumps({
                                "run_id": run_id,
                                "status": run_status[0],
                                "outcome": run_status[1],
                            }),
                        }
                        break
            except Exception:
                pass

            await asyncio.sleep(1.0)

    return EventSourceResponse(event_generator())
