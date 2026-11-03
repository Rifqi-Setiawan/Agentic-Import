
from pydantic import BaseModel


class ResetSafetyResult(BaseModel):
    allowed: bool
    rejection_reason: str | None = None


def evaluate_reset_safety(has_active_run: bool, company_id: int) -> ResetSafetyResult:
    """
    Evaluates whether demo reset is permitted:
    Demo reset is REJECTED if any active analysis run or job is currently executing.
    """
    if has_active_run:
        return ResetSafetyResult(
            allowed=False,
            rejection_reason="Reset ditolak: Masih terdapat pekerjaan analisis yang aktif untuk perusahaan ini.",
        )

    return ResetSafetyResult(
        allowed=True,
        rejection_reason=None,
    )
