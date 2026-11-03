from typing import Any


def apply_simulation_rule(
    shipment_state: dict[str, Any], new_rule_prefix: str, new_permit_code: str
) -> dict[str, Any]:
    """
    Applies regulatory simulation (e.g. new lartas rule on heading 8481 effective today):
    - Approved HS codes are preserved.
    - Compliance checklist & duties are updated.
    - If shipment is already submitted, status remains 'submitted', with badge 'needs_action_rule_change'.
    """
    updated = dict(shipment_state)
    updated_items = []
    has_matching_item = False

    clean_target = new_rule_prefix.replace(".", "").strip()

    for item in shipment_state.get("items", []):
        it = dict(item)
        item_hs = it.get("hs_code", "").replace(".", "").strip()
        if item_hs.startswith(clean_target):
            has_matching_item = True
            # Keep approved status and HS code intact!
        updated_items.append(it)

    updated["items"] = updated_items
    updated["new_requirements"] = [new_permit_code] if has_matching_item else []

    if has_matching_item:
        if updated.get("status") == "submitted":
            updated["needs_action_rule_change"] = True
        else:
            updated["needs_review"] = True

    return updated
