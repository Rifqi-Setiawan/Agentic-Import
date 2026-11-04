import json

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from src.api.deps import get_current_user, get_db_cursor
from src.core.security import verify_company_access

router = APIRouter(prefix="/clarifications", tags=["clarifications"])


class AnswerRequest(BaseModel):
    answer: str | None = None
    answer_text: str | None = None
    answer_source: str = "staff_form"  # staff_form, supplier_email, datasheet_upload

    @property
    def answer_value(self) -> str:
        return (self.answer or self.answer_text or "").strip()


@router.get("")
def list_clarifications(
    status: str | None = None,
    status_filter: str | None = None,
    user=Depends(get_current_user),
    cur=Depends(get_db_cursor),
):
    comp_id = int(user["company_id"])
    st = status_filter or status
    query = """
        SELECT cl.id, cl.shipment_id, cl.item_id, cl.question, cl.attribute,
               cl.reason, cl.status, cl.answer, cl.answer_source, cl.created_at, cl.answered_at
        FROM clarifications cl
        WHERE cl.company_id = %s
    """
    params = [comp_id]
    if st:
        query += " AND cl.status = %s"
        params.append(st)
    query += " ORDER BY cl.id DESC;"

    cur.execute(query, tuple(params))
    rows = cur.fetchall()

    clarifications = []
    for r in rows:
        clarifications.append({
            "id": str(r[0]),
            "shipment_id": str(r[1]) if r[1] else None,
            "item_id": str(r[2]) if r[2] else None,
            "question": r[3],
            "question_text": r[3],
            "attribute": r[4],
            "reason": r[5],
            "status": r[6],
            "answer": r[7],
            "answer_source": r[8],
            "channel": r[8] or "supplier",
            "created_at": r[9].isoformat() if r[9] else None,
            "answered_at": r[10].isoformat() if r[10] else None,
        })
    return {"clarifications": clarifications, "data": clarifications}


@router.post("/{clarification_id}/answer", status_code=status.HTTP_202_ACCEPTED)
def answer_clarification(
    clarification_id: str,
    req: AnswerRequest,
    user=Depends(get_current_user),
    cur=Depends(get_db_cursor)
):
    cur.execute("""
        SELECT cl.id, cl.company_id, cl.shipment_id, cl.item_id, cl.status, s.input_version
        FROM clarifications cl
        JOIN shipments s ON cl.shipment_id = s.id
        WHERE cl.id = %s;
    """, (int(clarification_id),))
    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Pertanyaan klarifikasi tidak ditemukan")

    cl_id, comp_id, shipment_id, item_id, current_status, input_ver = row
    verify_company_access(str(comp_id), user["company_id"])

    ans = req.answer_value
    if not ans:
        raise HTTPException(status_code=400, detail="Jawaban klarifikasi tidak boleh kosong")

    # 1. Update clarification
    new_version = input_ver + 1
    cur.execute("""
        UPDATE clarifications
        SET answer = %s, answer_source = %s, status = 'answered',
            answered_at = NOW()
        WHERE id = %s;
    """, (ans, req.answer_source, int(clarification_id)))

    # 2. Bump shipment input_version
    cur.execute("""
        UPDATE shipments
        SET input_version = %s, updated_at = NOW()
        WHERE id = %s;
    """, (new_version, shipment_id))

    # 3. Schedule items_subset continuation job
    dedupe_key = f"{comp_id}:{shipment_id}:answer:{clarification_id}:{new_version}"
    payload = json.dumps({
        "shipment_id": shipment_id,
        "target_item_ids": [item_id] if item_id else [],
        "version": new_version,
    })

    cur.execute("""
        INSERT INTO jobs (company_id, shipment_id, event_type, payload, dedupe_key, status, created_at)
        VALUES (%s, %s, 'items_subset', %s, %s, 'queued', NOW())
        ON CONFLICT (dedupe_key) DO UPDATE SET heartbeat_at = NOW()
        RETURNING id;
    """, (comp_id, shipment_id, payload, dedupe_key))
    job_row = cur.fetchone()
    job_id = job_row[0] if job_row else None

    return {
        "question_id": str(clarification_id),
        "job_id": str(job_id) if job_id else None,
        "next_run_id": None,
        "processing_status": "queued",
        "input_version": new_version,
        "target_item_id": str(item_id) if item_id else None
    }
