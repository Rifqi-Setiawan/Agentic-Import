from fastapi import APIRouter, Depends, HTTPException, Query
from src.api.deps import get_current_user, get_db_cursor
from src.core.catalog import get_official_hs_code, is_official_hs_code
from src.core.import_rates import verified_demo_rate

from src.services.hs_search import HS_SEARCH_COLUMNS, rank_hs_codes

router = APIRouter(prefix="/hs-codes", tags=["hs-codes"])


@router.get("/search")
def search_hs(
    q: str = Query(..., min_length=2),
    chapter: str | None = Query(None),
    limit: int = Query(10, ge=1, le=50),
    user=Depends(get_current_user),
    cur=Depends(get_db_cursor),
):
    cur.execute(f"""SELECT {HS_SEARCH_COLUMNS} FROM hs_codes
        WHERE %s::text IS NULL OR left(replace(hs_code, '.', ''), 2) = %s
        ORDER BY (hs_code=replace(hs_code,'.','')) DESC,hs_code""", (chapter, chapter))
    rows = (dict(zip(HS_SEARCH_COLUMNS.split(","), row, strict=True)) for row in cur.fetchall())
    data = []
    for row in rank_hs_codes(rows, q, limit):
        code_nodot = row["hs_code"]
        official_info = get_official_hs_code(code_nodot)
        bm = float(row["bm_rate"]) if row["bm_rate"] is not None else None
        tariff = verified_demo_rate(code_nodot, row["bm_rate"])
        data.append({
            "hs_code": code_nodot,
            "code_canonical": code_nodot,
            "description_id": row["description_id"],
            "description_en": row["description_en"],
            "bm_rate": bm,
            "rate_status": "verified_demo" if tariff else "demo_unverified" if bm is not None else "unverified",
            "rate_source": tariff["source"] if tariff else None,
            "lartas_coverage": row["lartas_coverage"] or "unknown",
            "source_url": official_info["source_url"] if official_info else None,
            "source_page": official_info["source_page"] if official_info else None,
            "lartas_verified": False,
            "current_rates_verified": False,
        })
    return {"data": data, "results": data}


@router.get("/{code}")
def get_hs_detail(
    code: str,
    user=Depends(get_current_user),
    cur=Depends(get_db_cursor),
):
    code_nodot = code.replace(".", "").strip()
    # Reject invalid legacy codes not in official BTKI 2022
    if not is_official_hs_code(code_nodot):
        raise HTTPException(status_code=404, detail=f"Kode HS {code} tidak ditemukan di referensi BTKI 2022.")

    official_info = get_official_hs_code(code_nodot)

    cur.execute("""
        SELECT hs_code, description_id, description_en, bm_rate, ppn_rate, pph_rate, lartas_coverage, source
        FROM hs_codes
        WHERE replace(hs_code, '.', '') = %s ORDER BY (hs_code=%s) DESC, id LIMIT 1;
    """, (code_nodot, code_nodot))
    row = cur.fetchone()

    # Fetch matching lartas rules scoped to global or current user company
    user_company_id = int(user["company_id"]) if user and user.get("company_id") else None
    cur.execute("""
        SELECT requirement_key, permit_name, issuing_agency, rule_group
        FROM lartas_rules
        WHERE %s LIKE replace(hs_prefix,'.','') || '%%' AND is_active = true AND effective_date<=NOW()
          AND (company_id IS NULL OR company_id = %s);
    """, (code_nodot, user_company_id))
    rules = cur.fetchall()

    bm_rate = float(row[3]) if row and row[3] is not None else None
    ppn_rate = float(row[4]) if row and row[4] is not None else None
    pph_rate = float(row[5]) if row and row[5] is not None else None
    tariff = verified_demo_rate(code_nodot, row[3]) if row else None

    return {
        "hs_code": row[0] if row else code_nodot,
        "code_canonical": code_nodot,
        "description_id": official_info["description_id"] if official_info else (row[1] if row else ""),
        "description_en": official_info["description_en"] if official_info else (row[2] if row else ""),
        "bm_rate": bm_rate,
        "ppn_rate": ppn_rate,
        "pph_rate": pph_rate,
        "rate_status": "verified_demo" if tariff else "demo_unverified" if bm_rate is not None else "unverified",
        "rate_source": tariff["source"] if tariff else None,
        "lartas_coverage": row[6] if row else "unknown",
        "source": "BTKI 2022 DJBC",
        "source_url": official_info["source_url"] if official_info else None,
        "source_page": official_info["source_page"] if official_info else None,
        "source_sha256": official_info["source_sha256"] if official_info else None,
        "lartas_verified": False,
        "current_rates_verified": False,
        "lartas_rules": [
            {
                "requirement_key": r[0],
                "permit_name": r[1],
                "agency": r[2],
                "rule_group": r[3],
            }
            for r in rules
        ],
    }
