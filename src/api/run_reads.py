"""Company-scoped read models for analysis history and persisted evidence."""
from fastapi import APIRouter, Depends, HTTPException

from src.api.deps import get_current_user, get_db_cursor
from src.core.security import verify_company_access

router = APIRouter(prefix="/shipments", tags=["analysis-history"])


def require_shipment(cur, shipment_id: int, user: dict) -> None:
    cur.execute("SELECT company_id FROM shipments WHERE id = %s", (shipment_id,))
    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Kiriman tidak ditemukan")
    verify_company_access(str(row[0]), str(user["company_id"]))


def read_runs(cur, shipment_id: int, company_id: int) -> list[dict]:
    cur.execute(
        """SELECT id, status, outcome, started_at, ended_at, total_tokens, cost_usd
           FROM agent_runs WHERE shipment_id = %s AND company_id = %s
           ORDER BY id DESC LIMIT 30""",
        (shipment_id, company_id),
    )
    return [
        {
            "id": str(row[0]), "status": row[1], "outcome": row[2],
            "created_at": row[3].isoformat() if row[3] else None,
            "ended_at": row[4].isoformat() if row[4] else None,
            "total_tokens": row[5],
            "cost_usd": str(row[6]) if row[6] is not None else None,
        }
        for row in cur.fetchall()
    ]


@router.get("/{shipment_id}/analysis")
def shipment_analysis(shipment_id: int, user=Depends(get_current_user), cur=Depends(get_db_cursor)):
    require_shipment(cur, shipment_id, user)
    company_id = int(user["company_id"])
    runs = read_runs(cur, shipment_id, company_id)
    cur.execute(
        """SELECT step.tool_output FROM agent_steps step
           JOIN agent_runs run ON run.id = step.run_id
           WHERE step.shipment_id = %s AND run.company_id = %s
             AND step.step_name = 'classification'
           ORDER BY step.id DESC LIMIT 1000""",
        (shipment_id, company_id),
    )
    latest = {}
    for row in cur.fetchall():
        payload = row[0]
        if isinstance(payload, dict) and payload.get("item_id") is not None:
            latest.setdefault(str(payload["item_id"]), payload)
    cur.execute(
        """SELECT SUM(cif_idr), SUM(bm_idr), SUM(ppn_idr), SUM(pph_idr),
                  SUM(total_duties_idr), COUNT(*)
           FROM duty_calculations
           WHERE shipment_id = %s AND company_id = %s AND is_current = true""",
        (shipment_id, company_id),
    )
    row = cur.fetchone()
    totals = None
    if row and row[5]:
        totals = {key: str(value) for key, value in zip(
            ("cif_idr", "bm_idr", "ppn_idr", "pph_idr", "total_duties_idr"), row[:5]
        )}
    return {"runs": runs, "classifications": latest, "totals": totals}
