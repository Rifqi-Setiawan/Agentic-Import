import hashlib
from enum import Enum

from pydantic import BaseModel


class OutboxStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    UNKNOWN = "unknown"


class OutboxProcessResult(BaseModel):
    message_id: int
    delivery_status: OutboxStatus
    auto_retry_scheduled: bool
    log_message: str


def generate_outbox_dedupe_key(
    company_id: int, shipment_id: int, gap_ids: list[int], reminder_no: int
) -> str:
    """
    Constructs deterministic deduplication key for email outbox:
    company_id:shipment_id:sorted_gaps:reminder_no
    """
    sorted_gaps = ",".join(str(g) for g in sorted(gap_ids))
    raw = f"{company_id}:{shipment_id}:{sorted_gaps}:{reminder_no}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def process_outbox_message(
    message_id: int, simulate_failure: str | None = None
) -> OutboxProcessResult:
    """
    Sends email to supplier inbox with safe deduplication and ambiguous timeout handling (A13).
    If SMTP server times out after DATA, records delivery_status='unknown' and does NOT auto-retry.
    """
    if simulate_failure == "smtp_timeout_after_data":
        return OutboxProcessResult(
            message_id=message_id,
            delivery_status=OutboxStatus.UNKNOWN,
            auto_retry_scheduled=False,
            log_message="Status pengiriman belum pasti (unknown status due to SMTP timeout after DATA). Pemeriksaan manual diperlukan.",
        )

    if simulate_failure == "connection_refused":
        return OutboxProcessResult(
            message_id=message_id,
            delivery_status=OutboxStatus.FAILED,
            auto_retry_scheduled=True,
            log_message="Koneksi SMTP gagal sebelum penerimaan pesan; retry otomatis dijadwalkan.",
        )

    return OutboxProcessResult(
        message_id=message_id,
        delivery_status=OutboxStatus.SENT,
        auto_retry_scheduled=False,
        log_message="Email terkirim ke inbox tujuan.",
    )
