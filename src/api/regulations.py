from fastapi import APIRouter, Depends
from pydantic import BaseModel

from src.api.deps import get_current_user, get_db_cursor

router = APIRouter(prefix="/regulations", tags=["regulations"])


class SimulateRequest(BaseModel):
    hs_prefix: str = "8481"
    requirement_code: str = "LS_NEW_2026"
    title: str = "Permendag No. 99/2026 — Verifikasi Teknis Tambahan Katup & Kran"


@router.post("/simulate-demo")
def simulate_demo_regulation(
    req: SimulateRequest,
    user=Depends(get_current_user),
    cur=Depends(get_db_cursor),
):
    """
    Enforces D07, A10, A16:
    Simulation affects user's company only.
    - MKN-007 (ready) -> flags needs_review / checklist updated
    - MKN-008 (submitted) -> keeps status submitted, sets needs_action_rule_change
    - MKN-003 (arrived) -> ignored
    """
    comp_id = int(user["company_id"])

    # 1. Check or insert simulated regulation
    cur.execute("""
        SELECT id FROM regulations
        WHERE company_id = %s AND is_simulation = true AND hs_prefix = %s;
    """, (comp_id, req.hs_prefix))
    existing = cur.fetchone()

    if not existing:
        cur.execute("""
            INSERT INTO regulations (company_id, regulation_number, title, hs_prefix, requirement_code, is_simulation, effective_date, created_at)
            VALUES (%s, %s, %s, %s, %s, true, NOW(), NOW())
            RETURNING id;
        """, (comp_id, "SIM-REG-8481-2026", req.title, req.hs_prefix, req.requirement_code))
        reg_id = cur.fetchone()[0]

        # Add corresponding lartas rule
        cur.execute("""
            INSERT INTO lartas_rules (company_id, hs_prefix, requirement_key, permit_name, issuing_agency, rule_group, is_active, effective_date, source)
            VALUES (%s, %s, %s, %s, 'Kemendag', 'LS_VALVE_GROUP', true, NOW(), 'Simulasi Demo');
        """, (comp_id, req.hs_prefix, req.requirement_code, req.title))
    else:
        reg_id = existing[0]

    # 2. Update affected shipments for company
    # Update MKN-007 (ready -> needs_review)
    cur.execute("""
        UPDATE shipments
        SET status = 'needs_review', readiness_status = 'incomplete', updated_at = NOW()
        WHERE company_id = %s AND shipment_number = 'MKN-007' AND status != 'arrived';
    """, (comp_id,))

    # Update MKN-008 (submitted -> stays submitted, flag action required)
    cur.execute("""
        UPDATE shipments
        SET needs_action_rule_change = true, updated_at = NOW()
        WHERE company_id = %s AND shipment_number = 'MKN-008';
    """, (comp_id,))

    return {
        "status": "success",
        "simulation_regulation_id": reg_id,
        "affected_prefix": req.hs_prefix,
        "requirement_code": req.requirement_code,
        "impact_summary": "Aturan simulasi aktif hari ini. MKN-007 ditandai perlu review ulang checklist, MKN-008 ditandai aksi perubahan aturan (tetap submitted), MKN-003 diabaikan.",
    }
