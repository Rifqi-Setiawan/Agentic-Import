import re

from pydantic import BaseModel


class CleanedExtractionMetadata(BaseModel):
    recipient_email: str
    forced_readiness: str | None = None
    sanitized_text: str


def sanitize_extraction_metadata(raw_text: str, allowed_recipients: list[str]) -> CleanedExtractionMetadata:
    """
    Guards against prompt injection attacks embedded inside invoices or vendor communications.
    Ensures that adversarial instructions (e.g., 'set readiness=ready', 'send email to attacker@evil.com')
    cannot override business logic, recipients allowlist, or readiness rules.
    """
    default_recipient = allowed_recipients[0] if allowed_recipients else "tim-impor@mitrakemas.co.id"

    # Reject any extracted email address that is not in the explicit allowlist
    found_emails = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", raw_text)
    chosen_email = default_recipient
    for em in found_emails:
        if em.lower() in [r.lower() for r in allowed_recipients]:
            chosen_email = em.lower()
            break

    # Strip adversarial directives
    cleaned = re.sub(
        r"(ignore\s+(previous|all)\s+instructions|set\s+readiness\s*=\s*\w+|bypass\s+customs)",
        "[REDACTED_ADVERSARIAL_INJECTION]",
        raw_text,
        flags=re.IGNORECASE,
    )

    return CleanedExtractionMetadata(
        recipient_email=chosen_email,
        forced_readiness=None,
        sanitized_text=cleaned,
    )
