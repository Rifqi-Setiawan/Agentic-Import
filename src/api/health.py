from datetime import UTC, datetime

from fastapi import APIRouter, Depends

from src.api.deps import get_db_cursor

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check(cur=Depends(get_db_cursor)):
    # 1. DB ping
    cur.execute("SELECT 1;")
    db_ok = cur.fetchone()[0] == 1

    # 2. Worker heartbeat
    cur.execute("SELECT MAX(heartbeat_at) FROM jobs;")
    row = cur.fetchone()
    last_worker_heartbeat = row[0].isoformat() if row and row[0] else None

    return {
        "status": "UP",
        "service": "imporjaga-api",
        "database": "connected" if db_ok else "unreachable",
        "worker_heartbeat": last_worker_heartbeat or "worker_active",
        "timestamp": datetime.now(UTC).isoformat(),
    }
