from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from src.api.deps import get_current_user, get_db_cursor
from src.core.security import verify_company_access

router = APIRouter(prefix="/reviews", tags=["reviews"])


class DecisionRequest(BaseModel):
    decision: str | None = None  # approve, modify, reject
    action: str | None = None
    modified_hs_code: str | None = None
    suggested_hs: str | None = None
    notes: str | None = None


@router.get("")
def list_reviews(
    status: str | None = None,
    status_filter: str | None = None,
    user=Depends(get_current_user),
    cur=Depends(get_db_cursor),
):
    comp_id = int(user["company_id"])
    st = status_filter or status
    query = """
        SELECT r.id, r.shipment_id, r.item_id, r.review_type, r.status, r.notes,
               i.description, i.hs_code_proposed, i.hs_code_accepted, r.created_at, r.decided_at
        FROM review_tasks r
        JOIN shipment_items i ON r.item_id = i.id
        WHERE r.company_id = %s
    """
    params = [comp_id]
    if st:
        if st in ("open", "pending"):
            query += " AND r.status IN ('open', 'pending')"
        else:
            query += " AND r.status = %s"
            params.append(st)
    query += " ORDER BY r.id DESC;"

    cur.execute(query, tuple(params))
    rows = cur.fetchall()

    reviews = []
    for r in rows:
        reviews.append({
            "id": str(r[0]),
            "shipment_id": str(r[1]) if r[1] else None,
            "item_id": str(r[2]) if r[2] else None,
            "review_type": r[3],
            "status": r[4],
            "notes": r[5],
            "decision_notes": r[5],
            "item_description": r[6],
            "suggested_hs_code": r[7] or r[8] or "",
            "created_at": r[9].isoformat() if r[9] else None,
            "decided_at": r[10].isoformat() if r[10] else None,
        })
    return {"reviews": reviews, "data": reviews}


@router.post("/{review_id}/decision")
def submit_review_decision(
    review_id: str,
    req: DecisionRequest,
    user=Depends(get_current_user),
    cur=Depends(get_db_cursor)
):
    user_role = user.get("role", "")
    if user_role not in ("ppjk_reviewer", "reviewer", "admin", "superadmin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hanya reviewer atau admin yang berwenang mengambil keputusan review",
        )

    cur.execute("""
        SELECT r.id, r.company_id, r.shipment_id, r.item_id, r.status,
               i.description, i.hs_code_accepted, i.hs_code_proposed
        FROM review_tasks r
        JOIN shipment_items i ON r.item_id = i.id
        WHERE r.id = %s;
    """, (int(review_id),))
    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Review task tidak ditemukan")

    r_id, comp_id, shipment_id, item_id, current_st, item_desc, hs_accepted, hs_proposed = row
    verify_company_access(str(comp_id), user["company_id"])

    decision_clean = (req.action or req.decision or "").strip().lower()
    if decision_clean not in ("approve", "modify", "reject"):
        raise HTTPException(status_code=400, detail="Keputusan harus 'approve', 'modify', atau 'reject'")

    if decision_clean == "reject":
        # Reject marks item as action_required / rejected
        cur.execute("""
            UPDATE review_tasks
            SET status = 'rejected', reviewer_id = %s, notes = %s, decided_at = NOW()
            WHERE id = %s;
        """, (int(user["id"]), req.notes, int(review_id)))

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
            "review_id": str(review_id),
            "status": "rejected",
            "action_required": True,
            "readiness_status": "blocked",
            "message": "Item ditolak oleh reviewer. Readiness kiriman diblokir (action_required)."
        }

    # Approve or Modify
    from src.core.catalog import is_official_hs_code

    final_hs = req.modified_hs_code or req.suggested_hs if decision_clean == "modify" else None
    if decision_clean == "modify":
        if not final_hs:
            raise HTTPException(status_code=400, detail="modified_hs_code wajib diisi jika keputusan 'modify'")
        clean_hs = final_hs.replace(".", "").strip()
        if len(clean_hs) != 8 or not clean_hs.isdigit():
            raise HTTPException(status_code=400, detail=f"Kode HS '{final_hs}' tidak valid. Harus 8 digit numerik.")
        if not is_official_hs_code(clean_hs):
            raise HTTPException(status_code=400, detail=f"Kode HS '{final_hs}' tidak ditemukan dalam katalog resmi BTKI")
        cur.execute("SELECT hs_code FROM hs_codes WHERE replace(hs_code, '.', '') = %s OR hs_code = %s LIMIT 1;", (clean_hs, final_hs))
        if not cur.fetchone():
            raise HTTPException(status_code=400, detail=f"Kode HS '{final_hs}' tidak ditemukan dalam katalog resmi BTKI")
        final_hs = clean_hs

    if decision_clean == "approve":
        final_hs = hs_accepted or hs_proposed
        if not final_hs:
            raise HTTPException(status_code=400, detail="Tidak ada kode HS usulan untuk disetujui")
        clean_hs = final_hs.replace(".", "").strip()
        if not is_official_hs_code(clean_hs):
            raise HTTPException(status_code=400, detail=f"Kode HS usulan '{final_hs}' tidak ditemukan dalam katalog resmi BTKI")
        final_hs = clean_hs

    # Update item status
    cur.execute("""
        UPDATE shipment_items
        SET status = 'approved', is_approved = true, hs_code_accepted = %s, updated_at = NOW()
        WHERE id = %s;
    """, (final_hs, item_id))

    # Update review task
    cur.execute("""
        UPDATE review_tasks
        SET status = %s, reviewer_id = %s, notes = %s, decided_at = NOW()
        WHERE id = %s;
    """, (decision_clean, int(user["id"]), req.notes, int(review_id)))

    # Record Human Decision in Classification Memory
    cur.execute("""
        INSERT INTO classification_memory (company_id, item_description, hs_code, decision_source, human_decision_notes, is_active, created_at)
        VALUES (%s, %s, %s, 'human_review', %s, true, NOW())
        RETURNING id;
    """, (comp_id, item_desc, final_hs, req.notes or f"Disetujui oleh {user['email']}"))

    import json
    cur.execute("""INSERT INTO jobs(company_id,shipment_id,event_type,dedupe_key,payload,status,created_at)
        VALUES(%s,%s,'review_decision',%s,%s,'queued',NOW()) ON CONFLICT(dedupe_key) DO NOTHING""",
        (comp_id, shipment_id, f"review:{review_id}:{decision_clean}", json.dumps({"mode":"recalc_only","target_item_ids":[item_id]})))

    return {
        "review_id": str(review_id),
        "status": decision_clean,
        "hs_code": final_hs,
        "memory_recorded": True,
        "message": f"Klasifikasi HS {final_hs} berhasil disetujui oleh reviewer."
    }
