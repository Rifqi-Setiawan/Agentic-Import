import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = ROOT / "data" / "reference" / "hs_codes_btki2022.json"
REGULATIONS_PATH = ROOT / "data" / "reference" / "regulations.json"

_CATALOG_CACHE: dict[str, dict[str, Any]] | None = None
_REGULATIONS_CACHE: list[dict[str, Any]] | None = None


def get_official_catalog() -> dict[str, dict[str, Any]]:
    global _CATALOG_CACHE
    if _CATALOG_CACHE is None:
        if CATALOG_PATH.exists():
            data = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
            _CATALOG_CACHE = {r["code"]: r for r in data.get("codes", [])}
        else:
            _CATALOG_CACHE = {}
    return _CATALOG_CACHE


def is_official_hs_code(code: str) -> bool:
    if not code:
        return False
    clean = code.replace(".", "").strip()
    return clean in get_official_catalog()


def get_official_hs_code(code: str) -> dict[str, Any] | None:
    if not code:
        return None
    clean = code.replace(".", "").strip()
    return get_official_catalog().get(clean)


def search_official_hs_catalog(query: str, chapter: str | None = None, limit: int = 10) -> list[dict[str, Any]]:
    catalog = get_official_catalog()
    q = query.strip().lower()
    q_nodot = q.replace(".", "")
    results = []

    for code, item in catalog.items():
        if chapter and not code.startswith(chapter):
            continue

        # Match by code, id description, or en description
        if (
            q in code
            or q_nodot in code
            or q in item["description_id"].lower()
            or q in item["description_en"].lower()
        ):
            results.append(item)
            if len(results) >= limit:
                break

    return results


def get_official_regulations() -> list[dict[str, Any]]:
    global _REGULATIONS_CACHE
    if _REGULATIONS_CACHE is None:
        if REGULATIONS_PATH.exists():
            data = json.loads(REGULATIONS_PATH.read_text(encoding="utf-8"))
            _REGULATIONS_CACHE = data.get("references", [])
        else:
            _REGULATIONS_CACHE = []
    return _REGULATIONS_CACHE
