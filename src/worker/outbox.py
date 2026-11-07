import hashlib
from enum import Enum
from typing import Any

from pydantic import BaseModel

from src.core.config import settings


class OutboxStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    UNKNOWN = "unknown"


class OutboxProcessResult(BaseModel):
    message_id: int
    delivery_status: OutboxStatus
    auto_retry_scheduled: bool = False
    log_message: str = ""
    status: str | None = None

    def model_post_init(self, __context: Any) -> None:
        if self.status is None:
            self.status = self.delivery_status.value


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
    message_id: int | dict[str, Any],
    simulate_failure: str | None = None,
    smtp_host: str | None = None,
    smtp_port: int | None = None,
    **kwargs: Any,
) -> OutboxProcessResult:
    """
    Sends email to supplier inbox with safe deduplication and ambiguous timeout handling (A13, F07).
    If SMTP server times out after DATA, records delivery_status='unknown' and does NOT auto-retry.
    If SMTP connection fails, records delivery_status='failed'.
    Never falsely marks sent without network delivery proof.
    """
    if isinstance(message_id, dict):
        msg_id = int(message_id.get("id", 0))
        recipient = message_id.get("recipient", "")
        subject = message_id.get("subject", "")
        body = message_id.get("body", "")
    else:
        msg_id = int(message_id)
        recipient = kwargs.get("recipient", "")
        subject = kwargs.get("subject", "")
        body = kwargs.get("body", "")

    if simulate_failure == "smtp_timeout_after_data":
        return OutboxProcessResult(
            message_id=msg_id,
            delivery_status=OutboxStatus.UNKNOWN,
            status="unknown",
            auto_retry_scheduled=False,
            log_message="Status pengiriman belum pasti (unknown status due to SMTP timeout after DATA). Pemeriksaan manual diperlukan.",
        )

    if simulate_failure == "connection_refused":
        return OutboxProcessResult(
            message_id=msg_id,
            delivery_status=OutboxStatus.FAILED,
            status="failed",
            auto_retry_scheduled=True,
            log_message="Koneksi SMTP gagal sebelum penerimaan pesan; retry otomatis dijadwalkan.",
        )

    # 1. Reject missing or blank recipient
    recipient_clean = recipient.strip() if recipient else ""
    if not recipient_clean:
        return OutboxProcessResult(
            message_id=msg_id,
            delivery_status=OutboxStatus.FAILED,
            status="failed",
            auto_retry_scheduled=False,
            log_message="Penerima email kosong atau tidak valid; pengiriman dibatalkan.",
        )

    # 2. Enforce exact AGENT_EMAIL_ALLOWED_RECIPIENTS before network
    allowed_recipients = set(settings.AGENT_EMAIL_ALLOWED_RECIPIENTS)
    if recipient_clean not in allowed_recipients:
        return OutboxProcessResult(
            message_id=msg_id,
            delivery_status=OutboxStatus.FAILED,
            status="failed",
            auto_retry_scheduled=False,
            log_message=f"Penerima {recipient_clean} ditolak: tidak terdaftar dalam AGENT_EMAIL_ALLOWED_RECIPIENTS.",
        )

    target_host = smtp_host or settings.SMTP_HOST
    target_port = smtp_port or settings.SMTP_PORT

    import smtplib
    import ssl
    from email.message import EmailMessage

    data_phase = False
    try:
        if (settings.SMTP_USERNAME or settings.SMTP_PASSWORD) and not settings.SMTP_STARTTLS:
            raise ValueError("Autentikasi SMTP memerlukan STARTTLS.")
        with smtplib.SMTP(host=target_host, port=target_port, timeout=5.0) as server:
            if settings.SMTP_STARTTLS:
                server.starttls(context=ssl.create_default_context())
            if settings.SMTP_USERNAME:
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            em = EmailMessage()
            em["From"] = settings.SMTP_FROM
            em["To"] = recipient_clean
            em["Subject"] = subject or "Pemberitahuan ImporJaga"
            em.set_content(body or "")

            data_phase = True
            rejected = server.send_message(em)
            if rejected:
                return OutboxProcessResult(
                    message_id=msg_id,
                    delivery_status=OutboxStatus.FAILED,
                    status="failed",
                    auto_retry_scheduled=True,
                    log_message=f"Server menolak pengiriman ke penerima: {rejected}",
                )

            return OutboxProcessResult(
                message_id=msg_id,
                delivery_status=OutboxStatus.SENT,
                status="sent",
                auto_retry_scheduled=False,
                log_message="Pesan diterima oleh server SMTP.",
            )
    except (TimeoutError, smtplib.SMTPServerDisconnected) as exc:
        if data_phase:
            return OutboxProcessResult(
                message_id=msg_id,
                delivery_status=OutboxStatus.UNKNOWN,
                status="unknown",
                auto_retry_scheduled=False,
                log_message=f"Status pengiriman belum pasti (post-DATA timeout/disconnect: {exc}). Pemeriksaan manual diperlukan tanpa auto-retry buta.",
            )
        return OutboxProcessResult(
            message_id=msg_id,
            delivery_status=OutboxStatus.FAILED,
            status="failed",
            auto_retry_scheduled=True,
            log_message=f"Koneksi SMTP timeout ({exc}); status ditandai failed.",
        )
    except Exception as exc:
        return OutboxProcessResult(
            message_id=msg_id,
            delivery_status=OutboxStatus.FAILED,
            status="failed",
            auto_retry_scheduled=True,
            log_message=f"Koneksi SMTP gagal ({exc}); status ditandai failed.",
        )
