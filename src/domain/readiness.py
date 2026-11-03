from enum import Enum
from typing import Any

from pydantic import BaseModel

from src.domain.lartas import LartasCoverage


class ReadinessStatus(str, Enum):
    READY = "ready"
    INCOMPLETE = "incomplete"
    BLOCKED = "blocked"


class ReadinessResult(BaseModel):
    ready: bool
    status: ReadinessStatus
    blocking_issues: list[str]
    warnings: list[str]
    item_count: int = 0
    document_count: int = 0


def evaluate_readiness(
    all_items_classified: bool = True,
    has_open_questions: bool = False,
    has_open_reviews: bool = False,
    documents_status: list[dict[str, Any]] | None = None,
    lartas_coverage: LartasCoverage = LartasCoverage.VERIFIED_RULES,
    has_unresolved_conflicts: bool = False,
    has_rejected_items: bool = False,
    has_out_of_scope: bool = False,
    has_pending_jobs: bool = False,
) -> ReadinessResult:
    """
    Single deterministic readiness evaluation engine as specified in docs/MVP-v1.1.md D06.
    """
    blocking_issues: list[str] = []
    warnings: list[str] = []

    # 1. Classification & Acceptance
    if not all_items_classified:
        blocking_issues.append("Belum semua barang memiliki keputusan klasifikasi yang valid.")
    if has_rejected_items:
        blocking_issues.append("Terdapat barang yang ditolak oleh reviewer (action_required).")
    if has_out_of_scope:
        blocking_issues.append("Terdapat barang yang berada di luar cakupan BTKI bab 33, 61, 62, 84, 85.")

    # 2. Questions
    if has_open_questions:
        blocking_issues.append("Terdapat pertanyaan klarifikasi yang belum dijawab.")

    # 3. Reviews
    if has_open_reviews:
        blocking_issues.append("Terdapat review klasifikasi atau kepatuhan yang masih terbuka.")

    # 4. Documents
    docs = documents_status or []
    for doc in docs:
        doc_type = doc.get("type", "Dokumen")
        doc_st = doc.get("status", "missing")
        if doc_st in ("missing", "pending"):
            blocking_issues.append(f"Dokumen persyaratan '{doc_type}' berstatus {doc_st} (belum lengkap).")

    # 5. Lartas Coverage & Conflicts
    if lartas_coverage == LartasCoverage.UNKNOWN:
        blocking_issues.append("Cakupan lartas berstatus 'unknown' (belum diverifikasi oleh ahli).")
    if has_unresolved_conflicts:
        blocking_issues.append("Terdapat konflik data regulasi lartas (DATA_CONFLICT) yang belum terselesaikan.")

    # 6. Active jobs
    if has_pending_jobs:
        blocking_issues.append("Masih terdapat pekerjaan analisis yang sedang berjalan atau diantrekan.")

    # Determine status
    if not blocking_issues:
        return ReadinessResult(
            ready=True,
            status=ReadinessStatus.READY,
            blocking_issues=[],
            warnings=warnings,
            item_count=len(docs),
            document_count=len(docs),
        )

    # If blocked conditions exist
    is_blocked = (
        has_rejected_items
        or has_out_of_scope
        or has_unresolved_conflicts
        or lartas_coverage == LartasCoverage.UNKNOWN
    )

    final_status = ReadinessStatus.BLOCKED if is_blocked else ReadinessStatus.INCOMPLETE

    return ReadinessResult(
        ready=False,
        status=final_status,
        blocking_issues=blocking_issues,
        warnings=warnings,
        item_count=len(docs),
        document_count=len(docs),
    )


def compute_pass_outcome(items_state: list[dict[str, Any]]) -> str:
    """
    Computes agent run pass outcome:
    - 'complete': all items classified and resolved
    - 'waiting_external': items waiting for supplier clarification
    - 'action_required': items rejected or need staff review
    """
    has_waiting = any(i.get("status") == "needs_clarification" for i in items_state)
    has_action = any(i.get("status") in ("rejected", "action_required") for i in items_state)

    if has_action:
        return "action_required"
    if has_waiting:
        return "waiting_external"
    return "complete"
