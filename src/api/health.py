from datetime import UTC, datetime
from fastapi import APIRouter, Depends
from src.api.deps import get_db_cursor
router=APIRouter(tags=["health"])
@router.get("/health")
def health_check(cur=Depends(get_db_cursor)):
    cur.execute("SELECT 1")
    connected=cur.fetchone()[0] == 1
    cur.execute("SELECT last_seen FROM worker_heartbeat WHERE id=1")
    row=cur.fetchone()
    now=datetime.now(UTC)
    seen=row[0] if row else None
    age=(now-seen).total_seconds() if seen else None
    return {"status":"UP" if connected and age is not None and age<=60 else "DEGRADED",
        "database":"connected" if connected else "unreachable", "service":"imporjaga-api",
        "worker_heartbeat":seen.isoformat() if seen else None,"worker_age_seconds":age,"timestamp":now.isoformat()}
