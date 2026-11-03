from enum import Enum

from pydantic import BaseModel


class ClassificationMode(str, Enum):
    ASSIST = "assist"
    AUTO = "auto"


class ClassificationCandidate(BaseModel):
    item_id: int
    hs_code: str
    confidence: float
    memory_match_score: float | None = None
    risk_level: str = "low"
    has_critic_warning: bool = False
    source_verified: bool = True
    attributes_compatible: bool = True


class ApprovalDecision(BaseModel):
    approved: bool
    requires_review: bool
    origin: str  # 'auto_rule_gate' or 'review_required'
    reason: str


def evaluate_approval_gate(cand: ClassificationCandidate, mode: ClassificationMode) -> ApprovalDecision:
    """
    Evaluates classification proposal under Assist vs Auto policy.
    - Assist: Always routes to Reviewer.
    - Auto: Requires confidence >= 0.85, memory match >= 0.92 with matching code,
      compatible attributes, no critic warning, verified source, low risk.
    """
    if mode == ClassificationMode.ASSIST:
        return ApprovalDecision(
            approved=False,
            requires_review=True,
            origin="review_required",
            reason="Mode Assist: Semua usulan klasifikasi HS baru memerlukan peninjauan staf/reviewer.",
        )

    # AUTO MODE
    if cand.has_critic_warning:
        return ApprovalDecision(
            approved=False,
            requires_review=True,
            origin="review_required",
            reason="Terdapat kritik atau catatan dari verifikator konsistensi.",
        )

    if cand.risk_level != "low":
        return ApprovalDecision(
            approved=False,
            requires_review=True,
            origin="review_required",
            reason=f"Tingkat risiko barang {cand.risk_level} (bukan low).",
        )

    if not cand.source_verified or not cand.attributes_compatible:
        return ApprovalDecision(
            approved=False,
            requires_review=True,
            origin="review_required",
            reason="Sumber data belum terverifikasi atau atribut teknis tidak kompatibel.",
        )

    if cand.confidence < 0.85:
        return ApprovalDecision(
            approved=False,
            requires_review=True,
            origin="review_required",
            reason=f"Skor keyakinan model ({cand.confidence:.2f}) di bawah ambang batas auto (0.85).",
        )

    if cand.memory_match_score is None:
        return ApprovalDecision(
            approved=False,
            requires_review=True,
            origin="review_required",
            reason="Tidak ditemukan memori keputusan manusia terdahulu yang relevan.",
        )

    if cand.memory_match_score < 0.92:
        return ApprovalDecision(
            approved=False,
            requires_review=True,
            origin="review_required",
            reason=f"Kecocokan memori manusia ({cand.memory_match_score:.2f}) di bawah ambang batas (0.92).",
        )

    # Auto-approved!
    return ApprovalDecision(
        approved=True,
        requires_review=False,
        origin="auto_rule_gate",
        reason="Persetujuan otomatis: Keyakinan >= 0.85, Memori Cocok >= 0.92, Risiko Low, Atribut Terverifikasi.",
    )
