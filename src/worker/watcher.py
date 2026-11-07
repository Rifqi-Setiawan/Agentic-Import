from typing import Any


def evaluate_shipment_watcher_eligibility(shipment: dict[str, Any], target_heading: str) -> bool:
    """
    Evaluates whether a shipment should be re-assessed by the regulatory watcher:
    - Analyzed shipments that have not yet arrived (ready, submitted, analyzing, etc.) -> TRUE if heading matches.
    - Arrived shipments -> FALSE (arrived shipments are not re-analyzed by watcher).
    """
    status = shipment.get("status", "").lower()
    if status == "arrived":
        return False

    shipment_heading = shipment.get("hs_heading", "").replace(".", "").strip()
    clean_target = target_heading.replace(".", "").strip()

    return bool(clean_target and shipment_heading.startswith(clean_target))


def find_affected_shipments_by_hs_prefix(
    company_id: int,
    hs_prefix: str,
    db: Any = None,
    cur: Any = None,
) -> list[dict[str, Any]]:
    """
    Finds active shipments (not arrived) for a company that have items matching hs_prefix.
    Supports either SQLAlchemy session (db) or raw database cursor (cur).
    """
    clean_prefix = hs_prefix.replace(".", "").strip()
    if not clean_prefix.isascii() or not clean_prefix.isdigit():
        return []
    results = []

    if db is not None:
        from src.models.entities import Shipment, ShipmentItem

        shipments = (
            db.query(Shipment)
            .join(ShipmentItem, ShipmentItem.shipment_id == Shipment.id)
            .filter(
                Shipment.company_id == company_id,
                Shipment.status != "arrived",
            )
            .all()
        )
        for s in shipments:
            has_matching_item = False
            for item in s.items:
                proposed = (item.hs_code_proposed or "").replace(".", "").strip()
                accepted = (item.hs_code_accepted or "").replace(".", "").strip()
                if proposed.startswith(clean_prefix) or accepted.startswith(clean_prefix):
                    has_matching_item = True
                    break
            if has_matching_item:
                results.append({
                    "shipment_id": s.id,
                    "shipment_number": s.shipment_number,
                    "status": s.status,
                    "readiness_status": s.readiness_status,
                })
        return results

    if cur is not None:
        cur.execute("""
            SELECT DISTINCT s.id, s.shipment_number, s.status, s.readiness_status
            FROM shipments s
            JOIN shipment_items i ON i.shipment_id = s.id AND i.company_id = s.company_id
            WHERE s.company_id = %s
              AND s.status != 'arrived'
              AND (
                  replace(COALESCE(i.hs_code_proposed, ''), '.', '') LIKE %s
                  OR replace(COALESCE(i.hs_code_accepted, ''), '.', '') LIKE %s
              );
        """, (int(company_id), f"{clean_prefix}%", f"{clean_prefix}%"))
        rows = cur.fetchall()
        for r in rows:
            results.append({
                "shipment_id": r[0],
                "shipment_number": r[1],
                "status": r[2],
                "readiness_status": r[3],
            })
        return results

    return results
