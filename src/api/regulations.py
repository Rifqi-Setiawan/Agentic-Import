from fastapi import APIRouter, Depends, HTTPException, status
from psycopg.types.json import Jsonb
from pydantic import BaseModel, Field

from src.api.deps import get_current_user, get_db_cursor
from src.worker.watcher import find_affected_shipments_by_hs_prefix

router = APIRouter(prefix="/regulations", tags=["regulations"])


@router.get("/references")
def list_reference_regulations(user=Depends(get_current_user)):
    from src.core.catalog import get_official_regulations
    refs = get_official_regulations()
    return {"references": refs, "data": refs}


@router.get("")
def list_regulations(
    user=Depends(get_current_user),
    cur=Depends(get_db_cursor),
):
    from src.core.catalog import get_official_regulations
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
    return {
        "regulations": regulations,
        "data": regulations,
        "official_references": get_official_regulations(),
    }


class SimulateRequest(BaseModel):
    hs_prefix: str = Field(default="8481", pattern=r"^[0-9]{2,8}$")
    requirement_code: str = Field(default="LS_NEW_2026", pattern=r"^[A-Z0-9_]{1,80}$")
    title: str = Field(default="SIMULASI — Verifikasi Teknis Tambahan Katup & Kran", min_length=1, max_length=250)


@router.post("/simulate-demo")
def simulate_demo_regulation(
    req: SimulateRequest,
    user=Depends(get_current_user),
    cur=Depends(get_db_cursor),
):
    user_role = user.get("role", "")
    if user_role not in ("admin", "superadmin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hanya admin yang berwenang melakukan simulasi perubahan regulasi",
        )

    comp_id = int(user["company_id"])

    # Verify company exists
    cur.execute("SELECT id FROM companies WHERE id = %s FOR NO KEY UPDATE;", (comp_id,))
    if not cur.fetchone():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perusahaan tidak ditemukan",
        )

    # 1. Check or insert simulated regulation
    cur.execute("""
        SELECT id FROM regulations
        WHERE company_id = %s AND is_simulation = true AND hs_prefix = %s
          AND requirement_code = %s ORDER BY id LIMIT 1;
    """, (comp_id, req.hs_prefix, req.requirement_code))
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
            VALUES (%s, %s, %s, %s, 'Kemendag', 'SIMULATION', true, NOW(), 'Simulasi Demo');
        """, (comp_id, req.hs_prefix, req.requirement_code, req.title))
    else:
        reg_id = existing[0]

    affected_list = find_affected_shipments_by_hs_prefix(company_id=comp_id, hs_prefix=req.hs_prefix, cur=cur)
    affected_list.sort(key=lambda shipment: shipment["shipment_id"])
    for aff in affected_list:
        s_id = aff["shipment_id"]
        cur.execute("""
            UPDATE shipments SET needs_action_rule_change=true, updated_at=NOW()
            WHERE id=%s AND company_id=%s AND status='submitted';
        """, (s_id, comp_id))
        cur.execute("""
            INSERT INTO jobs (shipment_id, company_id, event_type, dedupe_key, payload, status, created_at)
            VALUES (%s, %s, 'new_rule', %s, %s, 'queued', NOW())
            ON CONFLICT (dedupe_key) DO NOTHING;
        """, (s_id, comp_id, f"rule:{reg_id}:{s_id}", Jsonb({"mode": "recalc_only", "regulation_id": reg_id})))

    numbers = [shipment["shipment_number"] for shipment in affected_list]
    return {
        "status": "success",
        "simulation_regulation_id": reg_id,
        "affected_prefix": req.hs_prefix,
        "requirement_code": req.requirement_code,
        "affected_shipments": numbers,
        "impact_summary": f"{len(numbers)} kiriman aktif terdampak" + (f": {', '.join(numbers)}." if numbers else "."),
    }
