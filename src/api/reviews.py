import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.api.deps import get_current_user, get_db_cursor
from src.core.security import verify_company_access

router = APIRouter(prefix="/reviews", tags=["reviews"])


class DecisionRequest(BaseModel):
    decision: str  # approve, modify, reject
    modified_hs_code: str | None = None
    notes: str | None = None


@router.post("/{review_id}/decision")
def submit_review_decision(
    review_id: str,
    req: DecisionRequest,
    user=Depends(get_current_user),
    cur=Depends(get_db_cursor)
):
    cur.execute("""
        SELECT r.id, r.company_id, r.shipment_id, r.item_id, r.status, i.description_raw
        FROM review_tasks r
        JOIN shipment_items i ON r.item_id = i.id
        WHERE r.id = %s;
    """, (review_id,))
    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Review task tidak ditemukan")

    r_id, comp_id, shipment_id, item_id, current_st, item_desc = row
    verify_company_access(str(comp_id), user["company_id"])

    decision_clean = req.decision.lower()
    if decision_clean not in ("approve", "modify", "reject"):
        raise HTTPException(status_code=400, detail="Keputusan harus 'approve', 'modify', atau 'reject'")

    if decision_clean == "reject":
        # Reject marks item as action_required / rejected
        cur.execute("""
            UPDATE review_tasks
            SET status = 'rejected', reviewer_id = %s, notes = %s, decided_at = NOW()
            WHERE id = %s;
        """, (user["id"], req.notes, review_id))

        cur.execute("""
            UPDATE shipment_items
            SET status = 'rejected', updated_at = NOW()
            WHERE id = %s;
        """, (item_id,))

        cur.execute("""
            UPDATE shipments
            SET readiness_status = 'blocked', status = 'needs_review', updated_at = NOW()
            WHERE id = %s;
        """, (shipment_id,))

        return {
            "review_id": review_id,
            "status": "rejected",
            "action_required": True,
            "readiness_status": "blocked",
            "message": "Item ditolak oleh reviewer. Readiness kiriman diblokir (action_required)."
        }

    # Approve or Modify
    final_hs = req.modified_hs_code if decision_clean == "modify" else None
    if decision_clean == "modify" and not final_hs:
        raise HTTPException(status_code=400, detail="modified_hs_code wajib diisi jika keputusan 'modify'")

    if decision_clean == "approve":
        cur.execute("SELECT hs_code FROM hs_classifications WHERE item_id = %s AND is_current = true;", (item_id,))
        cls_row = cur.fetchone()
        final_hs = cls_row[0] if cls_row else "84223000"

    # Update item status
    cur.execute("""
        UPDATE shipment_items
        SET status = 'approved', updated_at = NOW()
        WHERE id = %s;
    """, (item_id,))

    # Update review task
    cur.execute("""
        UPDATE review_tasks
        SET status = %s, reviewer_id = %s, notes = %s, decided_at = NOW()
        WHERE id = %s;
    """, (decision_clean, user["id"], req.notes, review_id))

    # Record Human Decision in Classification Memory
    cur.execute("""
        INSERT INTO classification_memory (id, company_id, item_description, hs_code, decision_source, human_decision_notes, is_active, created_at)
        VALUES (%s, %s, %s, %s, 'human_review', %s, true, NOW());
    """, (str(uuid.uuid4()), comp_id, item_desc, final_hs, req.notes or f"Disetujui oleh {user['email']}"))

    return {
        "review_id": review_id,
        "status": decision_clean,
        "hs_code": final_hs,
        "memory_recorded": True,
        "message": f"Klasifikasi HS {final_hs} berhasil disetujui oleh reviewer."
    }
