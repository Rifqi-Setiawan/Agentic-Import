
from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.deps import get_current_user, get_db_cursor

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
    if chapter:
        cur.execute("""
            SELECT hs_code, description_id, description_en, bm_rate, lartas_coverage
            FROM hs_codes
            WHERE hs_code LIKE %s AND (description_id ILIKE %s OR description_en ILIKE %s OR hs_code ILIKE %s)
            LIMIT %s;
        """, (f"{chapter}%", clean_q, clean_q, clean_q, limit))
    else:
        cur.execute("""
            SELECT hs_code, description_id, description_en, bm_rate, lartas_coverage
            FROM hs_codes
            WHERE description_id ILIKE %s OR description_en ILIKE %s OR hs_code ILIKE %s
            LIMIT %s;
        """, (clean_q, clean_q, clean_q, limit))
    rows = cur.fetchall()

    data = []
    for r in rows:
        data.append({
            "hs_code": r[0],
            "description_id": r[1],
            "description_en": r[2],
            "bm_rate": float(r[3]),
            "lartas_coverage": r[4],
        })
    return {"data": data}


@router.get("/{code}")
def get_hs_detail(
    code: str,
    user=Depends(get_current_user),
    cur=Depends(get_db_cursor),
):
    cur.execute("""
        SELECT hs_code, description_id, description_en, bm_rate, ppn_rate, pph_rate, lartas_coverage, source
        FROM hs_codes
        WHERE hs_code = %s OR hs_code = %s;
    """, (code, code.replace(".", "")))
    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=f"Kode HS {code} tidak ditemukan di referensi BTKI.")

    # Fetch matching lartas rules
    clean_prefix = row[0][:4]
    cur.execute("""
        SELECT requirement_key, permit_name, issuing_agency, rule_group
        FROM lartas_rules
        WHERE hs_prefix = %s AND is_active = true;
    """, (clean_prefix,))
    rules = cur.fetchall()

    return {
        "hs_code": row[0],
        "description_id": row[1],
        "description_en": row[2],
        "bm_rate": float(row[3]),
        "ppn_rate": float(row[4]),
        "pph_rate": float(row[5]),
        "lartas_coverage": row[6],
        "source": row[7],
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
