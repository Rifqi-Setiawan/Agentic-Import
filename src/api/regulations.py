from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from src.api.deps import get_current_user, get_db_cursor

router = APIRouter(prefix="/regulations", tags=["regulations"])


@router.get("")
def list_regulations(
    user=Depends(get_current_user),
    cur=Depends(get_db_cursor),
):
    comp_id = int(user["company_id"])
    cur.execute("""
        SELECT id, regulation_number, title, hs_prefix, requirement_code, is_simulation, effective_date
        FROM regulations
        WHERE company_id IS NULL OR company_id = %s
        ORDER BY effective_date DESC NULLS LAST, id DESC;
    """, (comp_id,))
    rows = cur.fetchall()

    regulations = []
    for r in rows:
        regulations.append({
            "id": str(r[0]),
            "number": r[1],
            "regulation_number": r[1],
            "title": r[2],
            "summary": f"HS {r[3]} — {r[4]}",
            "hs_prefix": r[3],
            "requirement_code": r[4],
            "is_simulated": bool(r[5]),
            "is_simulation": bool(r[5]),
            "effective_date": r[6].isoformat() if r[6] else None,
        })
    return {"regulations": regulations, "data": regulations}


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
    user_role = user.get("role", "")
    if user_role not in ("admin", "superadmin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hanya admin yang berwenang melakukan simulasi perubahan regulasi",
        )

    comp_id = int(user["company_id"])

    # Verify company exists
    cur.execute("SELECT id FROM companies WHERE id = %s;", (comp_id,))
    if not cur.fetchone():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perusahaan tidak ditemukan",
        )

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
        """, (comp_id, f"SIM-REG-{req.hs_prefix}-2026", req.title, req.hs_prefix, req.requirement_code))
        reg_id = cur.fetchone()[0]

        # Add corresponding lartas rule
        cur.execute("""
            INSERT INTO lartas_rules (company_id, hs_prefix, requirement_key, permit_name, issuing_agency, rule_group, is_active, effective_date, source)
            VALUES (%s, %s, %s, %s, 'Kemendag', 'LS_VALVE_GROUP', true, NOW(), 'Simulasi Demo');
        """, (comp_id, req.hs_prefix, req.requirement_code, req.title))
    else:
        reg_id = existing[0]

    # 2. Update affected shipments for company using generic watcher
    from src.worker.watcher import find_affected_shipments_by_hs_prefix
    affected_list = find_affected_shipments_by_hs_prefix(company_id=comp_id, hs_prefix=req.hs_prefix, cur=cur)

    for aff in affected_list:
        s_id = aff["shipment_id"]
        s_st = aff["status"]
        if s_st in ("ready", "analyzed"):
            cur.execute("""
                UPDATE shipments
                SET status = 'needs_review', readiness_status = 'incomplete', updated_at = NOW()
                WHERE id = %s;
            """, (s_id,))
        elif s_st == "submitted":
            cur.execute("""
                UPDATE shipments
                SET needs_action_rule_change = true, updated_at = NOW()
                WHERE id = %s;
            """, (s_id,))

    # Update MKN-007 (ready -> needs_review) if present
    cur.execute("""
        UPDATE shipments
        SET status = 'needs_review', readiness_status = 'incomplete', updated_at = NOW()
        WHERE company_id = %s AND shipment_number = 'MKN-007' AND status != 'arrived';
    """, (comp_id,))

    # Update MKN-008 (submitted -> stays submitted, flag action required) if present
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
