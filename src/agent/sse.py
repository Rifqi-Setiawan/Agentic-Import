import json
from typing import Any


def format_sse_event(event_type: str, data: dict[str, Any], event_id: str) -> str:
    """
    Formats standard Server-Sent Event with id, event, and data fields.
    """
    payload = json.dumps(data, ensure_ascii=False)
    return f"id: {event_id}\nevent: {event_type}\ndata: {payload}\n\n"


def filter_events_after(events: list[dict[str, Any]], last_seq: int) -> list[dict[str, Any]]:
    """
    Deduplicates and filters stream events based on client Last-Event-ID / seq number.
    """
    return [e for e in events if e.get("seq", 0) > last_seq]
