import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from src.api.deps import get_current_user, get_db_cursor
from src.core.security import verify_company_access

router = APIRouter(prefix="/clarifications", tags=["clarifications"])


class AnswerRequest(BaseModel):
    answer: str
    answer_source: str = "staff_form"  # staff_form, supplier_email, datasheet_upload


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
    """, (clarification_id,))
    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Pertanyaan klarifikasi tidak ditemukan")

    cl_id, comp_id, shipment_id, item_id, current_status, input_ver = row
    verify_company_access(str(comp_id), user["company_id"])

    # 1. Update clarification
    new_version = input_ver + 1
    cur.execute("""
        UPDATE clarifications
        SET answer_text = %s, answer_source = %s, status = 'answered',
            answered_at = NOW(), answer_version = %s
        WHERE id = %s;
    """, (req.answer, req.answer_source, new_version, clarification_id))

    # 2. Bump shipment input_version
    cur.execute("""
        UPDATE shipments
        SET input_version = %s, updated_at = NOW()
        WHERE id = %s;
    """, (new_version, shipment_id))

    # 3. Schedule items_subset continuation job
    job_id = str(uuid.uuid4())
    dedupe_key = f"{comp_id}:{shipment_id}:answer:{clarification_id}:{new_version}"
    payload = f'{{"shipment_id": "{shipment_id}", "target_item_ids": ["{item_id}"], "version": {new_version}}}'

    cur.execute("""
        INSERT INTO jobs (id, company_id, shipment_id, job_type, payload_json, dedupe_key, status, attempts, max_attempts, scheduled_at, created_at, updated_at)
        VALUES (%s, %s, %s, 'items_subset', %s, %s, 'queued', 0, 3, NOW(), NOW(), NOW())
        ON CONFLICT (dedupe_key) DO NOTHING;
    """, (job_id, comp_id, shipment_id, payload, dedupe_key))

    return {
        "question_id": clarification_id,
        "job_id": job_id,
        "next_run_id": None,
        "processing_status": "queued",
        "input_version": new_version,
        "target_item_id": str(item_id) if item_id else None
    }
