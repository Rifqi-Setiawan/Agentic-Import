from enum import Enum

from pydantic import BaseModel


class LartasCoverage(str, Enum):
    VERIFIED_RULES = "verified_rules"
    VERIFIED_NONE = "verified_none"
    UNKNOWN = "unknown"


class LartasRule(BaseModel):
    id: int
    hs_prefix: str
    requirement_key: str
    rule_group: str
    supersedes_rule_id: int | None = None
    is_active: bool = True


class LartasMergeResult(BaseModel):
    active_requirements: list[str]
    has_conflict: bool = False
    conflict_details: str | None = None


def merge_lartas_rules(hs_code: str, rules: list[LartasRule]) -> LartasMergeResult:
    """
    Enforces D05:
    All matching lartas rules across prefixes are merged. Longest prefix only resolves
    curated variations within the same rule_group when explicit supersedes relation exists.
    If two conflicting requirements exist in the same rule_group without supersedes,
    flag DATA_CONFLICT and require human review.
    """
    clean_hs = hs_code.replace(".", "").strip()
    applicable_rules: list[LartasRule] = []

    for r in rules:
        clean_prefix = r.hs_prefix.replace(".", "").strip()
        if clean_hs.startswith(clean_prefix) and r.is_active:
            applicable_rules.append(r)

    # Group by rule_group
    grouped: dict[str, list[LartasRule]] = {}
    for r in applicable_rules:
        grouped.setdefault(r.rule_group, []).append(r)

    active_reqs: list[str] = []
    has_conflict = False
    conflict_notes: list[str] = []

    for group_name, group_rules in grouped.items():
        if len(group_rules) == 1:
            active_reqs.append(group_rules[0].requirement_key)
        else:
            # Check supersedes relation
            superseded_ids = {r.supersedes_rule_id for r in group_rules if r.supersedes_rule_id is not None}
            surviving = [r for r in group_rules if r.id not in superseded_ids]

            # If multiple rules still remain in the same group with different requirements
            distinct_reqs = {r.requirement_key for r in surviving}
            if len(distinct_reqs) > 1:
                has_conflict = True
                conflict_notes.append(f"Konflik pada kelompok aturan {group_name}: {distinct_reqs}")
            active_reqs.extend(distinct_reqs)

    return LartasMergeResult(
        active_requirements=sorted(set(active_reqs)),
        has_conflict=has_conflict,
        conflict_details="; ".join(conflict_notes) if conflict_notes else None,
    )
