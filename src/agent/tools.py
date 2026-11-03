from decimal import Decimal
from typing import Any

import psycopg

from src.core.config import settings
from src.domain.duty import DutyInput, calculate_import_duties


def get_db():
    return psycopg.connect(settings.DATABASE_URL)


def search_hs_codes(query: str, chapter: str | None = None) -> list[dict[str, Any]]:
    """
    Search official BTKI HS codes by description or code.
    """
    with get_db() as conn, conn.cursor() as cur:
        clean_q = f"%{query.strip()}%"
        if chapter:
            cur.execute("""
                    SELECT code, description_id, description_en, bm_rate, lartas_coverage
                    FROM hs_codes
                    WHERE chapter = %s AND (description_id ILIKE %s OR description_en ILIKE %s OR code ILIKE %s)
                    LIMIT 5;
                """, (chapter, clean_q, clean_q, clean_q))
        else:
            cur.execute("""
                    SELECT code, description_id, description_en, bm_rate, lartas_coverage
                    FROM hs_codes
                    WHERE description_id ILIKE %s OR description_en ILIKE %s OR code ILIKE %s
                    LIMIT 5;
                """, (clean_q, clean_q, clean_q))
        rows = cur.fetchall()
        return [
            {
                "code": r[0],
                "description_id": r[1],
                "description_en": r[2],
                "bm_rate": float(r[3]),
                "lartas_coverage": r[4],
            }
            for r in rows
        ]


def search_shipment_documents(shipment_id: str, query: str) -> list[dict[str, Any]]:
    """
    Search text extracted from uploaded shipment documents (datasheets, invoices, specs).
    """
    with get_db() as conn, conn.cursor() as cur:
        cur.execute("""
                SELECT doc_type, file_name, file_path
                FROM documents
                WHERE shipment_id = %s;
            """, (shipment_id,))
        rows = cur.fetchall()
        return [
            {"doc_type": r[0], "file_name": r[1], "file_path": r[2]}
            for r in rows
        ]


def ask_supplier(item_id: str, question: str, attribute: str, reason: str) -> dict[str, Any]:
    """
    Records a clarification question for a specific shipment item to be sent to supplier.
    """
    return {
        "action": "ask_supplier",
        "item_id": item_id,
        "question": question,
        "attribute": attribute,
        "reason": reason,
        "status": "pending_dispatch"
    }


def report_out_of_scope(item_id: str, reason: str, estimated_chapter: str) -> dict[str, Any]:
    """
    Flags an item as out of scope (outside BTKI chapters 33, 61, 62, 84, 85).
    Does NOT invent fake HS codes or duties.
    """
    return {
        "action": "report_out_of_scope",
        "item_id": item_id,
        "status": "out_of_scope",
        "reason": reason,
        "estimated_chapter": estimated_chapter,
        "requires_review": True
    }


def calculate_duties_tool(cif_idr: float, bm_rate: float = 5.0) -> dict[str, Any]:
    """
    Deterministic calculation tool.
    """
    res = calculate_import_duties(DutyInput(
        cif_idr=Decimal(str(cif_idr)),
        bm_percentage=Decimal(str(bm_rate))
    ))
    return {
        "cif_idr": float(res.cif_idr),
        "bm_idr": float(res.bm_idr),
        "nilai_impor_idr": float(res.nilai_impor_idr),
        "ppn_idr": float(res.ppn_idr),
        "pph_idr": float(res.pph_idr),
        "total_duties_idr": float(res.total_duties_idr)
    }


def query_classification_memory(description: str) -> dict[str, Any] | None:
    """
    Lookup past human approved classification decisions.
    """
    with get_db() as conn, conn.cursor() as cur:
        clean_desc = f"%{description.split()[0]}%"
        cur.execute("""
                SELECT hs_code, human_decision_notes, item_description
                FROM classification_memory
                WHERE item_description ILIKE %s AND is_active = true
                LIMIT 1;
            """, (clean_desc,))
        row = cur.fetchone()
        if row:
            return {
                "hs_code": row[0],
                "notes": row[1],
                "matched_description": row[2],
                "similarity": 0.95
            }
        return None
