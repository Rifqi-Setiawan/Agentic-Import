import json
import os
import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, Field

from src.api.deps import get_current_user, get_db_cursor
from src.core.config import settings
from src.core.security import verify_company_access
from src.domain.readiness import evaluate_readiness

router = APIRouter(prefix="/shipments", tags=["shipments"])


class CreateShipmentRequest(BaseModel):
    shipment_number: str | None = None
    reference_no: str | None = None
    supplier_name: str
    supplier_email: str
    currency: str = "USD"
    invoice_number: str | None = None
    cif_total_idr: Decimal = Field(default=Decimal("0"), ge=0)
    exchange_rate: Decimal | None = Field(default=None, gt=0)


@router.get("")
def list_shipments(user=Depends(get_current_user), cur=Depends(get_db_cursor)):
    cur.execute("""
        SELECT s.id, s.shipment_number, s.invoice_number, s.supplier_name, s.supplier_email,
               s.currency, s.cif_total_idr, s.status, s.readiness_status,
               s.input_version, s.submitted_at, s.arrived_at, s.created_at,
               (SELECT COUNT(*) FROM shipment_items WHERE shipment_id = s.id) as item_count
        FROM shipments s
        WHERE s.company_id = %s
        ORDER BY s.id ASC;
    """, (int(user["company_id"]),))
    rows = cur.fetchall()

    shipments = []
    for r in rows:
        shipments.append({
            "id": str(r[0]),
            "reference_no": r[1],
            "shipment_number": r[1],
            "invoice_no": r[2],
            "supplier_name": r[3],
            "supplier_email": r[4],
            "currency": r[5],
            "total_invoice_amount": float(r[6]) if r[6] else 0.0,
            "status": r[7],
            "readiness_status": r[8],
            "input_version": r[9],
            "submitted_at": r[10].isoformat() if r[10] else None,
            "arrived_at": r[11].isoformat() if r[11] else None,
            "created_at": r[12].isoformat() if r[12] else None,
            "item_count": r[13],
        })
    return {"shipments": shipments}


@router.post("", status_code=status.HTTP_201_CREATED)
def create_shipment(req: CreateShipmentRequest, user=Depends(get_current_user), cur=Depends(get_db_cursor)):
    ship_num = req.shipment_number or req.reference_no
    if not ship_num:
        ship_num = f"MKN-{uuid.uuid4().hex[:6].upper()}"

    supplier_email_clean = req.supplier_email.strip().lower()

    cur.execute("""
        INSERT INTO shipments (company_id, shipment_number, invoice_number, supplier_name, supplier_email,
                               currency, exchange_rate, cif_total_idr, total_duty_idr, status, readiness_status, input_version,
                               created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 0.0, 'draft', 'incomplete', 1, NOW(), NOW())
        RETURNING id, shipment_number, status;
    """, (
        int(user["company_id"]), ship_num, req.invoice_number,
        req.supplier_name, supplier_email_clean, req.currency, req.exchange_rate, req.cif_total_idr
    ))
    row = cur.fetchone()
    return {
        "id": row[0],
        "shipment_id": row[0],
        "reference_no": row[1],
        "shipment_number": row[1],
        "status": row[2],
    }


def _get_classification_evidence(cur, shipment_id: int) -> dict[int, dict]:
    """
    Returns mapping of item_id -> {rationale, citations, alternatives, attributes, hs_code}
    from latest agent_steps with step_name='classification' for this shipment.
    """
    cur.execute("""
        SELECT tool_output
        FROM agent_steps
        WHERE shipment_id = %s AND step_name = 'classification'
        ORDER BY id DESC;
    """, (shipment_id,))
    rows = cur.fetchall()
    evidence_by_item: dict[int, dict] = {}
    for (out_raw,) in rows:
        if not out_raw:
            continue
        try:
            out = json.loads(out_raw) if isinstance(out_raw, str) else out_raw
        except Exception:
            continue

        if isinstance(out, dict):
            if "item_id" in out:
                try:
                    iid = int(out["item_id"])
                    if iid not in evidence_by_item:
                        evidence_by_item[iid] = out
                except (ValueError, TypeError):
                    pass
            if "items" in out and isinstance(out["items"], list):
                for sub in out["items"]:
                    if isinstance(sub, dict) and "item_id" in sub:
                        try:
                            iid = int(sub["item_id"])
                            if iid not in evidence_by_item:
                                evidence_by_item[iid] = sub
                        except (ValueError, TypeError):
                            pass
        elif isinstance(out, list):
            for sub in out:
                if isinstance(sub, dict) and "item_id" in sub:
                    try:
                        iid = int(sub["item_id"])
                        if iid not in evidence_by_item:
                            evidence_by_item[iid] = sub
                    except (ValueError, TypeError):
                        pass
    return evidence_by_item


@router.get("/{shipment_id}")
def get_shipment_detail(shipment_id: str, user=Depends(get_current_user), cur=Depends(get_db_cursor)):
    # 1. Fetch shipment
    cur.execute("""
        SELECT s.id, s.company_id, s.shipment_number, s.invoice_number, s.supplier_name, s.supplier_email,
               s.currency, s.cif_total_idr, s.status, s.readiness_status, s.input_version,
               s.submitted_at, s.arrived_at, s.created_at
        FROM shipments s
        WHERE s.id = %s;
    """, (int(shipment_id),))
    s_row = cur.fetchone()
    if not s_row:
        raise HTTPException(status_code=404, detail="Kiriman tidak ditemukan")

    # Multi-tenant verification (A01)
    verify_company_access(resource_company_id=int(s_row[1]), current_user_company_id=int(user["company_id"]))

    # Active run lookup for trace picker
    cur.execute("""
        SELECT id FROM agent_runs
        WHERE shipment_id = %s AND company_id = %s
        ORDER BY (status = 'running') DESC, id DESC
        LIMIT 1;
    """, (int(shipment_id), int(user["company_id"])))
    run_row = cur.fetchone()
    active_run_id = str(run_row[0]) if run_row else None

    # 2. Fetch items & classification evidence
    evidence_by_item = _get_classification_evidence(cur, int(shipment_id))

    cur.execute("""
        SELECT i.id, i.line_no, i.description, i.quantity, i.uom, i.unit_price, i.total_price_cif, i.status,
               i.hs_code_proposed, i.confidence_score, i.is_approved
        FROM shipment_items i
        WHERE i.shipment_id = %s
        ORDER BY i.line_no ASC;
    """, (int(shipment_id),))
    items_rows = cur.fetchall()

    items = []
    has_rejected = False
    has_out_of_scope = False
    all_classified = len(items_rows) > 0

    for it in items_rows:
        it_id = int(it[0])
        it_status = it[7]
        is_appr = it[10]
        if it_status == "rejected":
            has_rejected = True
        if it_status == "out_of_scope":
            has_out_of_scope = True
        if not is_appr or it_status in ("draft", "needs_clarification") or not it[8]:
            all_classified = False

        ev = evidence_by_item.get(it_id, {})
        rat = ev.get("rationale") or f"Klasifikasi pos tarif {it[8] or ''} berdasarkan uraian barang dan kecocokan BTKI 2022."
        cits = ev.get("citations") or []
        alts = ev.get("alternatives") or []
        attrs = ev.get("attributes") or {}

        items.append({
            "id": str(it[0]),
            "line_no": it[1],
            "item_number": it[1],
            "description": it[2],
            "qty": float(it[3]),
            "quantity": float(it[3]),
            "unit": it[4],
            "uom": it[4],
            "unit_price": float(it[5]),
            "price_amount": float(it[5]),
            "total_price": float(it[6]),
            "total_price_cif": float(it[6]),
            "status": it_status,
            "hs_code": it[8],
            "hs_code_proposed": it[8],
            "confidence_score": float(it[9]) if it[9] is not None else None,
            "is_approved": is_appr,
            "rationale": rat,
            "justification": rat,
            "citations": cits,
            "alternatives": alts,
            "attributes": attrs,
            "classification": {
                "hs_code": it[8],
                "rationale": rat,
                "citations": cits,
                "alternatives": alts,
                "attributes": attrs,
            },
        })

    # 3. Fetch documents
    cur.execute("""
        SELECT d.id, d.doc_type, d.file_name, d.file_size, d.status, d.uploaded_at
        FROM documents d
        WHERE d.shipment_id = %s
        ORDER BY d.uploaded_at ASC;
    """, (int(shipment_id),))
    doc_rows = cur.fetchall()
    documents = []
    for d in doc_rows:
        documents.append({
            "id": str(d[0]),
            "type": d[1],
            "file_name": d[2],
            "file_size": d[3],
            "status": d[4],
            "uploaded_at": d[5].isoformat() if d[5] else None,
        })

    # 4. Fetch clarifications
    cur.execute("""
        SELECT cl.id, cl.item_id, cl.question, cl.status, cl.attribute, cl.reason, cl.answer
        FROM clarifications cl
        WHERE cl.shipment_id = %s;
    """, (int(shipment_id),))
    clarif_rows = cur.fetchall()
    clarifications = []
    has_open_questions = False
    for c in clarif_rows:
        if c[3] == "open":
            has_open_questions = True
        clarifications.append({
            "id": str(c[0]),
            "item_id": str(c[1]) if c[1] else None,
            "question": c[2],
            "status": c[3],
            "attribute": c[4],
            "reason": c[5],
            "answer": c[6],
        })

    # 5. Evaluate Readiness Deterministically (D06)
    readiness_eval = evaluate_readiness(
        all_items_classified=all_classified,
        has_open_questions=has_open_questions,
        has_open_reviews=False,
        documents_status=documents,
        has_rejected_items=has_rejected,
        has_out_of_scope=has_out_of_scope,
        has_pending_jobs=False,
    )

    return {
        "id": str(s_row[0]),
        "reference_no": s_row[2],
        "shipment_number": s_row[2],
        "invoice_no": s_row[3],
        "supplier_name": s_row[4],
        "supplier_email": s_row[5],
        "currency": s_row[6],
        "total_invoice_amount": float(s_row[7]) if s_row[7] else 0.0,
        "status": s_row[8],
        "readiness_status": readiness_eval.status.value,
        "is_ready": readiness_eval.ready and s_row[9] == "ready",
        "blocking_issues": readiness_eval.blocking_issues,
        "warnings": readiness_eval.warnings,
        "active_run_id": active_run_id,
        "pending_job_count": 0,
        "input_version": s_row[10],
        "submitted_at": s_row[11].isoformat() if s_row[11] else None,
        "arrived_at": s_row[12].isoformat() if s_row[12] else None,
        "created_at": s_row[13].isoformat() if s_row[13] else None,
        "items": items,
        "documents": documents,
        "clarifications": clarifications,
    }


@router.post("/{shipment_id}/mark-submitted")
def mark_shipment_submitted(shipment_id: str, user=Depends(get_current_user), cur=Depends(get_db_cursor)):
    cur.execute("SELECT company_id, status FROM shipments WHERE id = %s FOR UPDATE;", (int(shipment_id),))
    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Kiriman tidak ditemukan")

    verify_company_access(int(row[0]), int(user["company_id"]))

    # 1. Check open reviews
    cur.execute("SELECT id FROM review_tasks WHERE shipment_id = %s AND status IN ('open', 'pending');", (int(shipment_id),))
    has_open_reviews = len(cur.fetchall()) > 0

    # 2. Check checklist items
    cur.execute("SELECT requirement_code, status FROM checklist_items WHERE shipment_id = %s;", (int(shipment_id),))
    checklist_rows = cur.fetchall()
    has_missing_checklist = any(r[1] in ("missing", "pending", "required") for r in checklist_rows)

    # 3. Check active jobs
    cur.execute("SELECT id FROM jobs WHERE shipment_id = %s AND status IN ('queued', 'processing');", (int(shipment_id),))
    has_pending_jobs = len(cur.fetchall()) > 0

    # 4. Check documents
    cur.execute("SELECT status FROM documents WHERE shipment_id = %s;", (int(shipment_id),))
    docs = [{"status": r[0]} for r in cur.fetchall()]
    if not docs or has_missing_checklist:
        docs.append({"status": "missing"})

    # 5. Check items
    cur.execute("SELECT status FROM shipment_items WHERE shipment_id = %s;", (int(shipment_id),))
    items_st = [r[0] for r in cur.fetchall()]

    # 6. Check clarifications
    cur.execute("SELECT status FROM clarifications WHERE shipment_id = %s AND status = 'open';", (int(shipment_id),))
    has_open_q = len(cur.fetchall()) > 0

    all_classified = len(items_st) > 0 and all(s == "approved" for s in items_st)

    readiness = evaluate_readiness(
        all_items_classified=all_classified and not has_open_reviews,
        has_open_questions=has_open_q,
        documents_status=docs,
        has_rejected_items=any(s == "rejected" for s in items_st),
        has_open_reviews=has_open_reviews,
        has_pending_jobs=has_pending_jobs,
    )

    if not readiness.ready:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": "Kiriman belum memenuhi syarat readiness untuk diajukan.",
                "blocking_issues": readiness.blocking_issues,
            },
        )

    cur.execute("""
        UPDATE shipments
        SET status = 'submitted', submitted_at = NOW(), updated_at = NOW()
        WHERE id = %s RETURNING id, status, submitted_at;
    """, (int(shipment_id),))
    res = cur.fetchone()
    return {"id": str(res[0]), "status": res[1], "submitted_at": res[2].isoformat()}


@router.post("/{shipment_id}/upload")
@router.post("/{shipment_id}/documents")
async def upload_document(
    shipment_id: str,
    file: UploadFile = File(...),
    doc_type: str = Form("INVOICE"),
    user=Depends(get_current_user),
    cur=Depends(get_db_cursor),
):
    cur.execute("SELECT company_id, input_version FROM shipments WHERE id = %s;", (int(shipment_id),))
    s_row = cur.fetchone()
    if not s_row:
        raise HTTPException(status_code=404, detail="Kiriman tidak ditemukan")

    verify_company_access(int(s_row[0]), int(user["company_id"]))

    content = await file.read()

    # 1. Size check: max 10MB
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Ukuran berkas melebihi batas 10MB",
        )

    # 2. PDF type validation: magic bytes %PDF-
    if not content.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Hanya berkas format PDF yang diizinkan (magic bytes %PDF-)",
        )

    filename_lower = (file.filename or "").lower()
    if not filename_lower.endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Nama berkas harus berakhiran .pdf",
        )

    os.makedirs(settings.STORAGE_VAULT_PATH, exist_ok=True)
    doc_uuid = str(uuid.uuid4())
    safe_name = f"{doc_uuid}_{file.filename}"
    file_path = os.path.join(settings.STORAGE_VAULT_PATH, safe_name)

    with open(file_path, "wb") as f:
        f.write(content)

    doc_type_clean = (doc_type or "INVOICE").strip().lower()
    doc_type_map = {
        "invoice": "INVOICE",
        "packing_list": "PACKING_LIST",
        "spec": "DATASHEET",
        "datasheet": "DATASHEET",
        "bill_of_lading": "BL",
        "bl": "BL",
        "permit": "LARTAS_PERMIT",
        "lartas_permit": "LARTAS_PERMIT",
        "insurance": "INSURANCE",
    }
    normalized_doc_type = doc_type_map.get(doc_type_clean, doc_type.upper())

    cur.execute("""
        INSERT INTO documents (shipment_id, company_id, doc_type, file_name, file_path, file_size, status, uploaded_at)
        VALUES (%s, %s, %s, %s, %s, %s, 'provided', NOW())
        RETURNING id;
    """, (int(shipment_id), int(user["company_id"]), normalized_doc_type, file.filename, file_path, len(content)))
    doc_id = cur.fetchone()[0]

    # Increment input_version and auto-queue analysis job
    import json
    cur.execute("""
        UPDATE shipments
        SET input_version = input_version + 1, updated_at = NOW()
        WHERE id = %s
        RETURNING input_version;
    """, (int(shipment_id),))
    new_version = cur.fetchone()[0]

    cur.execute("""
        INSERT INTO jobs (shipment_id, company_id, event_type, dedupe_key, status, payload, created_at, updated_at)
        VALUES (%s, %s, 'analyze_shipment', %s, 'queued', %s, NOW(), NOW())
        RETURNING id;
    """, (
        int(shipment_id),
        int(user["company_id"]),
        f"analyze:{shipment_id}:v{new_version}",
        json.dumps({"shipment_id": int(shipment_id), "document_id": doc_id, "version": new_version})
    ))
    job_id = cur.fetchone()[0]

    return {
        "document_id": str(doc_id),
        "file_name": file.filename,
        "file_size": len(content),
        "status": "provided",
        "input_version": new_version,
        "job_id": str(job_id),
    }


@router.get("/{shipment_id}/documents")
def list_shipment_documents(
    shipment_id: str,
    user=Depends(get_current_user),
    cur=Depends(get_db_cursor),
):
    cur.execute("SELECT company_id FROM shipments WHERE id = %s;", (int(shipment_id),))
    s_row = cur.fetchone()
    if not s_row:
        raise HTTPException(status_code=404, detail="Kiriman tidak ditemukan")
    verify_company_access(int(s_row[0]), int(user["company_id"]))

    cur.execute("""
        SELECT id, doc_type, file_name, file_size, status, uploaded_at
        FROM documents
        WHERE shipment_id = %s
        ORDER BY uploaded_at ASC;
    """, (int(shipment_id),))
    rows = cur.fetchall()
    docs = []
    for d in rows:
        docs.append({
            "id": str(d[0]),
            "type": d[1],
            "doc_type": d[1],
            "file_name": d[2],
            "file_size": d[3],
            "status": d[4],
            "uploaded_at": d[5].isoformat() if d[5] else None,
        })
    return {"documents": docs, "data": docs}


@router.get("/{shipment_id}/items")
def list_shipment_items(
    shipment_id: str,
    user=Depends(get_current_user),
    cur=Depends(get_db_cursor),
):
    cur.execute("SELECT company_id FROM shipments WHERE id = %s;", (int(shipment_id),))
    s_row = cur.fetchone()
    if not s_row:
        raise HTTPException(status_code=404, detail="Kiriman tidak ditemukan")
    verify_company_access(int(s_row[0]), int(user["company_id"]))

    evidence_by_item = _get_classification_evidence(cur, int(shipment_id))

    cur.execute("""
        SELECT id, line_no, description, quantity, uom, unit_price, total_price_cif,
               hs_code_proposed, hs_code_accepted, confidence_score, risk_level, status, is_approved
        FROM shipment_items
        WHERE shipment_id = %s
        ORDER BY line_no ASC, id ASC;
    """, (int(shipment_id),))
    rows = cur.fetchall()
    items = []
    for r in rows:
        it_id = int(r[0])
        ev = evidence_by_item.get(it_id, {})
        rat = ev.get("rationale") or f"Klasifikasi pos tarif {r[7] or ''} berdasarkan uraian barang dan kecocokan BTKI 2022."
        cits = ev.get("citations") or []
        alts = ev.get("alternatives") or []
        attrs = ev.get("attributes") or {}

        items.append({
            "id": str(r[0]),
            "line_no": r[1],
            "item_number": r[1],
            "description": r[2],
            "quantity": float(r[3]) if r[3] is not None else 0.0,
            "uom": r[4],
            "price_amount": float(r[5]) if r[5] is not None else 0.0,
            "unit_price": float(r[5]) if r[5] is not None else 0.0,
            "total_price_cif": float(r[6]) if r[6] is not None else 0.0,
            "hs_code_proposed": r[7],
            "hs_code_accepted": r[8],
            "confidence_score": float(r[9]) if r[9] is not None else 0.0,
            "risk_level": r[10],
            "status": r[11],
            "is_approved": bool(r[12]),
            "rationale": rat,
            "justification": rat,
            "citations": cits,
            "alternatives": alts,
            "attributes": attrs,
            "classification": {
                "hs_code": r[7],
                "rationale": rat,
                "citations": cits,
                "alternatives": alts,
                "attributes": attrs,
            },
        })
    return {"items": items, "data": items}


@router.get("/{shipment_id}/checklist")
def get_shipment_checklist(
    shipment_id: str,
    user=Depends(get_current_user),
    cur=Depends(get_db_cursor),
):
    cur.execute("SELECT company_id FROM shipments WHERE id = %s;", (int(shipment_id),))
    s_row = cur.fetchone()
    if not s_row:
        raise HTTPException(status_code=404, detail="Kiriman tidak ditemukan")
    verify_company_access(int(s_row[0]), int(user["company_id"]))

    cur.execute("""
        SELECT id, item_id, requirement_code, title, agency, status, required_before_submission, resolution_reason
        FROM checklist_items
        WHERE shipment_id = %s
        ORDER BY id ASC;
    """, (int(shipment_id),))
    rows = cur.fetchall()
    checklist = []
    for r in rows:
        checklist.append({
            "id": str(r[0]),
            "item_id": str(r[1]) if r[1] else None,
            "requirement_code": r[2],
            "title": r[3],
            "agency": r[4],
            "status": r[5],
            "required_before_submission": bool(r[6]),
            "resolution_reason": r[7],
        })
    return {"checklist": checklist, "data": checklist}


@router.get("/{shipment_id}/runs")
def list_shipment_runs(
    shipment_id: str,
    user=Depends(get_current_user),
    cur=Depends(get_db_cursor),
):
    cur.execute("SELECT company_id FROM shipments WHERE id = %s;", (int(shipment_id),))
    s_row = cur.fetchone()
    if not s_row:
        raise HTTPException(status_code=404, detail="Kiriman tidak ditemukan")
    verify_company_access(int(s_row[0]), int(user["company_id"]))

    cur.execute("""
        SELECT id, status, outcome, total_tokens, cost_usd, started_at, ended_at, created_at
        FROM agent_runs
        WHERE shipment_id = %s AND company_id = %s
        ORDER BY id DESC;
    """, (int(shipment_id), int(user["company_id"])))
    rows = cur.fetchall()
    runs = []
    for r in rows:
        runs.append({
            "id": str(r[0]),
            "status": r[1],
            "outcome": r[2],
            "total_tokens": r[3],
            "cost_usd": float(r[4]) if r[4] is not None else None,
            "started_at": r[5].isoformat() if r[5] else None,
            "ended_at": r[6].isoformat() if r[6] else None,
            "created_at": r[7].isoformat() if r[7] else None,
        })
    return {"runs": runs, "data": runs}


@router.get("/{shipment_id}/pib")
@router.get("/{shipment_id}/pib-draft")
def get_shipment_pib(
    shipment_id: str,
    user=Depends(get_current_user),
    cur=Depends(get_db_cursor),
):
    cur.execute("""
        SELECT s.id, s.shipment_number, s.supplier_name, s.currency,
               s.status, s.readiness_status, c.name, c.npwp, s.cif_total_idr
        FROM shipments s
        JOIN companies c ON s.company_id = c.id
        WHERE s.id = %s AND s.company_id = %s;
    """, (int(shipment_id), int(user["company_id"])))
    s_row = cur.fetchone()
    if not s_row:
        raise HTTPException(status_code=404, detail="Kiriman tidak ditemukan")

    cur.execute("""
        SELECT cif_idr, bm_percentage, bm_idr, ppn_percentage, ppn_idr, pph_percentage, pph_idr, total_duties_idr
        FROM duty_calculations
        WHERE shipment_id = %s AND is_current = true
        ORDER BY id DESC LIMIT 1;
    """, (int(shipment_id),))
    d_row = cur.fetchone()

    cif_val = float(d_row[0]) if d_row and d_row[0] is not None else 0.0
    bm_val = float(d_row[2]) if d_row and d_row[2] is not None else 0.0
    ppn_val = float(d_row[4]) if d_row and d_row[4] is not None else 0.0
    pph_val = float(d_row[6]) if d_row and d_row[6] is not None else 0.0
    total_val = float(d_row[7]) if d_row and d_row[7] is not None else 0.0

    if total_val == 0.0 and len(s_row) > 8 and s_row[8] and float(s_row[8]) > 0.0:
        from decimal import Decimal
        from src.domain.duty import DutyInput, calculate_import_duties
        calc = calculate_import_duties(DutyInput(cif_idr=Decimal(str(s_row[8]))))
        cif_val = float(calc.cif_idr)
        bm_val = float(calc.bm_idr)
        ppn_val = float(calc.ppn_idr)
        pph_val = float(calc.pph_idr)
        total_val = float(calc.total_duties_idr)

    pib_data = {
        "shipment_id": str(s_row[0]),
        "shipment_number": s_row[1],
        "importer_name": s_row[6],
        "importer_npwp": s_row[7],
        "supplier_name": s_row[2],
        "origin_country": "CN",
        "currency": s_row[3],
        "status": s_row[4],
        "readiness_status": s_row[5],
        "cif_idr": cif_val,
        "bm_idr": bm_val,
        "ppn_idr": ppn_val,
        "pph_idr": pph_val,
        "total_duties_idr": total_val,
    }
    return {"pib_draft": pib_data, "data": pib_data}


@router.get("/{shipment_id}/messages")
def get_shipment_messages(
    shipment_id: str,
    user=Depends(get_current_user),
    cur=Depends(get_db_cursor),
):
    cur.execute("SELECT company_id FROM shipments WHERE id = %s;", (int(shipment_id),))
    s_row = cur.fetchone()
    if not s_row:
        raise HTTPException(status_code=404, detail="Kiriman tidak ditemukan")
    verify_company_access(int(s_row[0]), int(user["company_id"]))

    cur.execute("""
        SELECT id, recipient, subject, body, delivery_status, sent_at, created_at
        FROM messages
        WHERE shipment_id = %s
        ORDER BY created_at ASC;
    """, (int(shipment_id),))
    rows = cur.fetchall()
    messages = []
    for r in rows:
        messages.append({
            "id": str(r[0]),
            "recipient": r[1],
            "subject": r[2],
            "body": r[3],
            "delivery_status": r[4],
            "sent_at": r[5].isoformat() if r[5] else None,
            "created_at": r[6].isoformat() if r[6] else None,
        })
    return {"messages": messages, "data": messages}


@router.post("/{shipment_id}/analyze")
def trigger_analysis(
    shipment_id: str,
    user=Depends(get_current_user),
    cur=Depends(get_db_cursor),
):
    cur.execute("SELECT id, company_id, input_version, status FROM shipments WHERE id = %s;", (int(shipment_id),))
    s_row = cur.fetchone()
    if not s_row:
        raise HTTPException(status_code=404, detail="Kiriman tidak ditemukan")

    verify_company_access(int(s_row[1]), int(user["company_id"]))
    comp_id = int(s_row[1])
    input_ver = s_row[2]

    # Check if there is already an active run (queued or running)
    cur.execute("""
        SELECT id FROM agent_runs
        WHERE shipment_id = %s AND status IN ('queued', 'running');
    """, (int(shipment_id),))
    active = cur.fetchone()
    if active:
        return {
            "status": "already_running",
            "run_id": str(active[0]),
            "message": "Analisis agen sedang berjalan untuk kiriman ini.",
        }

    # Queue job for background worker
    dedupe_key = f"{comp_id}:{shipment_id}:full_analysis:{input_ver}:{uuid.uuid4()}"
    payload = json.dumps({"shipment_id": int(shipment_id), "version": input_ver})
    cur.execute("""
        INSERT INTO jobs (company_id, shipment_id, event_type, payload, dedupe_key, status, created_at)
        VALUES (%s, %s, 'full_analysis', %s, %s, 'queued', NOW())
        RETURNING id;
    """, (comp_id, int(shipment_id), payload, dedupe_key))
    job_id = cur.fetchone()[0]

    # Update shipment status to analyzing
    cur.execute("""
        UPDATE shipments
        SET status = 'analyzing', updated_at = NOW()
        WHERE id = %s;
    """, (int(shipment_id),))

    return {
        "status": "queued",
        "job_id": str(job_id),
        "shipment_id": str(shipment_id),
        "message": "Analisis kepabeanan berhasil dijadwalkan ke worker agen.",
    }
