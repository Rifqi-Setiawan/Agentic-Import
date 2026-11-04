from fastapi import APIRouter, Depends, HTTPException, Query
from src.api.deps import get_current_user, get_db_cursor
from src.core.catalog import get_official_hs_code, is_official_hs_code

router = APIRouter(prefix="/hs-codes", tags=["hs-codes"])


@router.get("/search")
def search_hs(
    q: str = Query(..., min_length=2),
    chapter: str | None = Query(None),
    limit: int = Query(10, ge=1, le=50),
    user=Depends(get_current_user),
    cur=Depends(get_db_cursor),
):
    clean_q = f"%{q.strip()}%"
    clean_nodot = f"%{q.strip().replace('.', '')}%"
    if chapter:
        cur.execute("""
            SELECT hs_code, description_id, description_en, bm_rate, lartas_coverage
            FROM hs_codes
            WHERE hs_code LIKE %s AND (description_id ILIKE %s OR description_en ILIKE %s OR hs_code ILIKE %s OR replace(hs_code, '.', '') ILIKE %s)
            LIMIT %s;
        """, (f"{chapter}%", clean_q, clean_q, clean_q, clean_nodot, limit * 2))
    else:
        cur.execute("""
            SELECT hs_code, description_id, description_en, bm_rate, lartas_coverage
            FROM hs_codes
            WHERE description_id ILIKE %s OR description_en ILIKE %s OR hs_code ILIKE %s OR replace(hs_code, '.', '') ILIKE %s
            LIMIT %s;
        """, (clean_q, clean_q, clean_q, clean_nodot, limit * 2))
    rows = cur.fetchall()

    data = []
    for r in rows:
        code_nodot = r[0].replace(".", "").strip()
        # Enforce catalog membership: exclude invalid legacy codes like 33012910
        if not is_official_hs_code(code_nodot):
            continue
        official_info = get_official_hs_code(code_nodot)
        bm = float(r[3]) if r[3] is not None else None
        data.append({
            "hs_code": r[0],
            "description_id": official_info["description_id"] if official_info else r[1],
            "description_en": official_info["description_en"] if official_info else r[2],
            "bm_rate": bm,
            "rate_status": "demo_unverified" if bm is not None else "unverified",
            "lartas_coverage": r[4] or "unknown",
            "source_url": official_info["source_url"] if official_info else None,
            "source_page": official_info["source_page"] if official_info else None,
            "lartas_verified": False,
            "current_rates_verified": False,
        })
        if len(data) >= limit:
            break
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
        WHERE replace(hs_code, '.', '') = %s OR hs_code = %s;
    """, (code_nodot, code))
    row = cur.fetchone()

    # Fetch matching lartas rules
    clean_prefix = code_nodot[:4]
    cur.execute("""
        SELECT requirement_key, permit_name, issuing_agency, rule_group
        FROM lartas_rules
        WHERE hs_prefix = %s AND is_active = true;
    """, (clean_prefix,))
    rules = cur.fetchall()

    bm_rate = float(row[3]) if row and row[3] is not None else None
    ppn_rate = float(row[4]) if row and row[4] is not None else None
    pph_rate = float(row[5]) if row and row[5] is not None else None

    return {
        "hs_code": row[0] if row else code_nodot,
        "code_canonical": code_nodot,
        "description_id": official_info["description_id"] if official_info else (row[1] if row else ""),
        "description_en": official_info["description_en"] if official_info else (row[2] if row else ""),
        "bm_rate": bm_rate,
        "ppn_rate": ppn_rate,
        "pph_rate": pph_rate,
        "rate_status": "demo_unverified" if bm_rate is not None else "unverified",
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
