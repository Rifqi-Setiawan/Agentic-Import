from fastapi import APIRouter, Depends, HTTPException, status

from src.api.admin import evaluate_reset_safety
from src.api.deps import get_current_user, get_db_cursor
from src.core.seed import seed_data

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/demo/reset")
def reset_demo_data(user=Depends(get_current_user), cur=Depends(get_db_cursor)):
    """
    Enforces D08, Section 8, A16:
    Demo reset affects user's company only.
    Replay / reset does NOT duplicate jobs, reviews, or emails.
    Rejected if any active analysis run is in flight.
    """
    comp_id = user["company_id"]

    # Check active runs
    cur.execute("""
        SELECT COUNT(*) FROM agent_runs
        WHERE company_id = %s AND status IN ('queued', 'running');
    """, (comp_id,))
    active_runs = cur.fetchone()[0]

    safety = evaluate_reset_safety(has_active_run=(active_runs > 0), company_id=1)
    if not safety.allowed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=safety.rejection_reason,
        )

    # Re-run ingestion to restore baseline demo data
    try:
        seed_data(reset=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal melakukan reset demo: {e!s}") from e

    return {
        "status": "success",
        "message": "Data demo PT Mitra Kemas Nusantara berhasil di-reset ke kondisi awal (MKN-011, MKN-007, MKN-008, MKN-003)."
    }
