from typing import Any


def create_continuation_job(shipment_id: int, answered_item_id: int, question_id: int) -> dict[str, Any]:
    """
    Creates continuation job for a specific answered item:
    Runs items_subset without re-analyzing unaffected items.
    """
    return {
        "shipment_id": shipment_id,
        "event_type": "items_subset",
        "target_item_ids": [answered_item_id],
        "question_id": question_id,
        "status": "queued",
    }


def should_queue_or_debounce(
    active_run_id: int | None, incoming_event_time: float, last_event_time: float
) -> dict[str, Any]:
    """
    Enforces single active run guarantee per shipment.
    Events arriving while a run is active are debounced (10s) and queued as pending jobs.
    """
    if active_run_id is not None:
        return {
            "action": "debounce_and_queue",
            "active_run_id": active_run_id,
            "debounce_seconds": 10,
        }
    return {
        "action": "start_run_immediately",
        "active_run_id": None,
    }
