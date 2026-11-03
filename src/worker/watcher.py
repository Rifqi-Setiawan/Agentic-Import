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

    return bool(clean_target in shipment_heading or shipment_heading.startswith(clean_target))
