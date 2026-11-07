from fastapi import APIRouter, Depends, HTTPException, status
from psycopg import sql

from src.api.admin import evaluate_reset_safety
from src.api.deps import get_current_user, get_db_cursor
from src.core.config import settings

router = APIRouter(prefix="/admin", tags=["admin"])


def seed_data(cur, company_id):
    from scripts.import_reference_catalog import import_fixtures

    import_fixtures(cur.connection, company_id, interactive=True)
    cur.execute("""INSERT INTO shipments (company_id,shipment_number,supplier_name,supplier_email,
        currency,status,readiness_status,input_version,created_at,updated_at)
        VALUES (%s,'MKN-DEMO-UPLOAD','Pemasok Demo','tim-impor@mitrakemas.example',
        'USD','draft','incomplete',1,NOW(),NOW())""", (company_id,))


@router.post("/demo/reset")
def reset_demo_data(user=Depends(get_current_user), cur=Depends(get_db_cursor)):
    """
    Enforces D08, Section 8, A16:
    Demo reset affects user's company only.
    Replay / reset does NOT duplicate jobs, reviews, or emails.
    Rejected if any active analysis run is in flight.
    """
    user_role = user.get("role", "")
    if user_role not in ("admin", "superadmin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hanya admin yang memiliki wewenang untuk mereset data demo",
        )

    comp_id = int(user["company_id"])
    if comp_id != settings.DEMO_COMPANY_ID:
        raise HTTPException(status_code=403, detail="Reset hanya tersedia di workspace demo yang dikonfigurasi.")

    cur.execute("SELECT id FROM companies WHERE id=%s FOR UPDATE", (comp_id,))
    if not cur.fetchone():
        raise HTTPException(status_code=404, detail="Workspace demo tidak ditemukan.")
    cur.execute("SELECT id FROM shipments WHERE company_id=%s ORDER BY id FOR UPDATE", (comp_id,))
    shipment_ids = [row[0] for row in cur.fetchall()]
    cur.execute("""
        SELECT EXISTS (SELECT 1 FROM agent_runs WHERE company_id=%s AND status IN ('queued','running'))
            OR EXISTS (SELECT 1 FROM jobs WHERE company_id=%s AND status IN ('queued','processing'));
    """, (comp_id, comp_id))
    active_runs = cur.fetchone()[0]

    safety = evaluate_reset_safety(has_active_run=(active_runs > 0), company_id=comp_id)
    if not safety.allowed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=safety.rejection_reason,
        )

    for table in ("checklist_items", "duty_calculations", "clarifications", "review_tasks",
                  "agent_steps", "agent_runs", "jobs", "messages", "documents", "shipment_items"):
        cur.execute(sql.SQL("DELETE FROM {} WHERE shipment_id=ANY(%s)").format(sql.Identifier(table)),
                    (shipment_ids,))
    cur.execute("DELETE FROM shipments WHERE company_id=%s", (comp_id,))
    seed_data(cur=cur, company_id=comp_id)

    return {
        "status": "success",
        "message": "Skenario demo dan satu kiriman kosong sudah dimuat ulang."
    }
