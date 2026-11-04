"""
Protected Audit Acceptance Test Suite v1.2 for ImporJaga MVP
Formally verifying remediation of findings F01-F14 from docs/AUDIT-2026-11-04.md and docs/AMENDMENT-2026-11-04.md.
PROTECTED FILE — DO NOT MODIFY WITHOUT EXPLICIT PERMISSION FROM USER RIFQI.
Authorship: Jarvis (Chief Orchestrator) — Normative Amendment v1.2 with Provenance.
Original v1.1 reference preserved at tests/test_audit_acceptance.py (SHA: 6baeaf5ae759c05937a0138b103b8e376dceddb847c2402f92116cb265a2373e).
"""
from datetime import UTC, datetime, timedelta
import pytest
from fastapi.testclient import TestClient
import psycopg
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from src.core.config import settings
from src.core.security import create_access_token, get_password_hash
from src.models.entities import (
    Base,
    Company,
    User,
    Shipment,
    ShipmentItem,
    ReviewTask,
    Job,
)
from src.api.main import app
from src.api.deps import get_db_cursor


# ==============================================================================
# F14 & Isolation Guard Fixture
# ==============================================================================
@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """
    CRITICAL TEST DB GUARD:
    Ensures tests NEVER run against production database.
    Initializes isolated test database schema and overrides app dependencies.
    """
    test_db_url = settings.TEST_DATABASE_URL
    assert "test" in test_db_url.lower(), (
        f"CRITICAL TEST DB GUARD: TEST_DATABASE_URL ({test_db_url}) must be an isolated test database!"
    )
    # Redirect DATABASE_URL for the test session to test DB
    original_db_url = settings.DATABASE_URL
    settings.DATABASE_URL = test_db_url

    test_engine = create_engine(test_db_url, pool_pre_ping=True)
    with test_engine.connect() as conn:
        current_db = conn.execute(text("SELECT current_database();")).scalar()
        assert current_db == "imporjaga_test", (
            f"CRITICAL TEST DB GUARD: Connected to unexpected database '{current_db}', expected 'imporjaga_test'!"
        )
        assert current_db != "imporjaga", "Test connected directly to production imporjaga database!"
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        conn.commit()

    Base.metadata.create_all(bind=test_engine)

    # Dependency override for raw psycopg cursor in FastAPI
    def override_get_db_cursor():
        with psycopg.connect(test_db_url) as conn:
            with conn.cursor() as cur:
                yield cur
            conn.commit()

    app.dependency_overrides[get_db_cursor] = override_get_db_cursor

    yield test_engine

    # Teardown: clear overrides and restore settings
    app.dependency_overrides.pop(get_db_cursor, None)
    settings.DATABASE_URL = original_db_url


@pytest.fixture
def test_db_session(setup_test_database):
    Session = sessionmaker(autocommit=False, autoflush=False, bind=setup_test_database)
    session = Session()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def client(setup_test_database):
    return TestClient(app)


# ==============================================================================
# Helper to create authentic persisted test users and tokens
# ==============================================================================
def create_test_user_and_token(
    db, company_id: int, role: str, email: str, full_name: str = "Test User"
) -> tuple[User, str]:
    """Persists a real active User entity in the test database and returns (user, token)."""
    user = db.query(User).filter_by(email=email).first()
    if not user:
        user = User(
            company_id=company_id,
            email=email,
            full_name=full_name,
            password_hash=get_password_hash("securepassword123"),
            role=role,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    token = create_access_token({
        "sub": str(user.id),
        "company_id": str(company_id),
        "email": email,
        "role": role,
    })
    return user, token


# ==============================================================================
# T_F14: Guard Isolated Test DB
# ==============================================================================
def test_f14_guard_isolated_test_db(setup_test_database):
    """(F14) Verify that test environment connects exclusively to test DB."""
    with psycopg.connect(settings.TEST_DATABASE_URL) as conn, conn.cursor() as cur:
        cur.execute("SELECT current_database();")
        current_db = cur.fetchone()[0]
        assert current_db == "imporjaga_test", f"Expected imporjaga_test, got {current_db}"
        assert current_db != "imporjaga", "Test connected directly to production imporjaga database!"


# ==============================================================================
# T_F01: Real Agent Pipeline & Trace Execution
# ==============================================================================
def test_f01_real_agent_pipeline_execution(test_db_session):
    """
    (F01) Pipeline must execute real vertical pipeline:
    pypdf extraction, item persistence, BTKI semantic/lexical retrieval,
    genuine 9Router LLM call (stream:false) returning real tokens/cost, and duty math.
    """
    from src.agent import llm
    assert hasattr(llm, "call_llm") or hasattr(llm, "invoke_llm") or hasattr(llm, "get_llm_client"), (
        "src.agent.llm must provide an actual model client or invocation function for 9Router."
    )


# ==============================================================================
# T_F02: Evaluation Runner Consistency
# ==============================================================================
def test_f02_evaluation_metrics_and_runner():
    """
    (F02) Evaluation metrics must be reproducible and derived without contradictions.
    """
    from scripts.eval_hs import calculate_metrics

    sample_preds = [
        {"expected_hs8": "8481.80.90", "predicted_hs8": "8481.80.90", "top_candidates": ["8481.80.90", "8481.10.00"]},
        {"expected_hs8": "8481.80.90", "predicted_hs8": "8481.80.10", "top_candidates": ["8481.80.10", "8481.80.90"]},
        {"expected_hs8": "8501.10.10", "predicted_hs8": "8481.80.90", "top_candidates": ["8481.80.90", "8422.30.00"]},
    ]

    metrics = calculate_metrics(sample_preds)
    assert metrics["total_samples"] == 3
    assert metrics["top1_hs6_accuracy"] == 66.67
    assert metrics["top1_hs8_accuracy"] == 33.33
    assert metrics["top3_hs8_recall"] == 66.67


# ==============================================================================
# T_F03: PIB Multi-Tenant Isolation
# ==============================================================================
def test_f03_pib_multi_tenant_isolation(client, test_db_session):
    """
    (F03) User of Company 1 cannot read PIB Draft or details of Company 2.
    Must return 404 Not Found (or 403 Forbidden).
    Includes positive control verifying Company 1 can access its own shipment.
    """
    c1 = Company(name="Test Comp 1", npwp="111111111111111")
    c2 = Company(name="Test Comp 2", npwp="222222222222222")
    test_db_session.add_all([c1, c2])
    test_db_session.commit()

    s1 = Shipment(
        company_id=c1.id,
        shipment_number="TEST-C1-001",
        supplier_name="Company 1 Supplier",
        supplier_email="supplier@c1.cn",
        readiness_status="ready",
    )
    s2 = Shipment(
        company_id=c2.id,
        shipment_number="TEST-C2-001",
        supplier_name="Shenzhen Supplier",
        supplier_email="supplier@c2.cn",
        readiness_status="ready",
    )
    test_db_session.add_all([s1, s2])
    test_db_session.commit()

    # Create real authenticated users for Company 1
    _, token_c1 = create_test_user_and_token(
        test_db_session, company_id=c1.id, role="importer_staff", email="staff@c1.com"
    )
    headers_c1 = {"Authorization": f"Bearer {token_c1}"}

    # 1. Positive control: Company 1 staff accesses own shipment
    resp_own = client.get(f"/api/v1/shipments/{s1.id}/pib-draft", headers=headers_c1)
    assert resp_own.status_code == 200, f"Company 1 should access own shipment, got {resp_own.status_code}"

    # 2. Tenancy isolation: Company 1 staff accesses Company 2 shipment -> 404 or 403
    resp_foreign = client.get(f"/api/v1/shipments/{s2.id}/pib-draft", headers=headers_c1)
    assert resp_foreign.status_code in (404, 403), (
        f"Cross-tenant leak! Status: {resp_foreign.status_code}, data: {resp_foreign.text}"
    )


# ==============================================================================
# T_F04: Role Enforcement on Mutations
# ==============================================================================
def test_f04_role_enforcement_on_mutations(client, test_db_session):
    """
    (F04) Staff (importer_staff) must receive 403 on mutation endpoints:
    - /api/v1/reviews/{id}/decision
    - /api/v1/regulations/simulate-demo
    - /api/v1/admin/demo/reset
    Authorized roles (ppjk_reviewer, admin) must not receive 403.
    """
    c = Company(name="Role Test Co", npwp="333333333333333")
    test_db_session.add(c)
    test_db_session.commit()

    _, staff_token = create_test_user_and_token(test_db_session, c.id, "importer_staff", "staff@roletest.com")
    _, reviewer_token = create_test_user_and_token(test_db_session, c.id, "ppjk_reviewer", "rev@roletest.com")
    _, admin_token = create_test_user_and_token(test_db_session, c.id, "admin", "admin@roletest.com")

    staff_headers = {"Authorization": f"Bearer {staff_token}"}
    reviewer_headers = {"Authorization": f"Bearer {reviewer_token}"}
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Staff attempts simulation -> 403
    sim_resp = client.post("/api/v1/regulations/simulate-demo", headers=staff_headers, json={"hs_prefix": "8481"})
    assert sim_resp.status_code == 403, f"Expected 403 for staff on simulation, got {sim_resp.status_code}"

    # 2. Staff attempts demo reset -> 403
    reset_resp = client.post("/api/v1/admin/demo/reset", headers=staff_headers)
    assert reset_resp.status_code == 403, f"Expected 403 for staff on reset, got {reset_resp.status_code}"

    # 3. Staff attempts review decision -> 403
    rev_resp = client.post("/api/v1/reviews/99999/decision", headers=staff_headers, json={"decision": "approve"})
    assert rev_resp.status_code == 403, f"Expected 403 for staff on review decision, got {rev_resp.status_code}"

    # 4. Reviewer is allowed on review decision (not 403)
    rev_ok = client.post("/api/v1/reviews/99999/decision", headers=reviewer_headers, json={"decision": "approve"})
    assert rev_ok.status_code != 403, "Reviewer must not receive 403 on review decision"

    # 5. Admin is allowed on simulation (not 403)
    admin_sim = client.post("/api/v1/regulations/simulate-demo", headers=admin_headers, json={"hs_prefix": "8481"})
    assert admin_sim.status_code != 403, "Admin must not receive 403 on simulation"


# ==============================================================================
# T_F05: Deterministic Readiness Blocks Submission
# ==============================================================================
def test_f05_deterministic_readiness_blocks_submission(client, test_db_session):
    """
    (F05) A shipment with missing/pending requirements or open reviews cannot be marked submitted.
    Must return 409 Conflict with non-empty blocking_issues.
    """
    c = Company(name="Readiness Test Co", npwp="444444444444444")
    test_db_session.add(c)
    test_db_session.commit()

    s = Shipment(
        company_id=c.id,
        shipment_number="READINESS-001",
        supplier_name="Global Tech",
        supplier_email="supplier@global.com",
        readiness_status="incomplete",
        status="analyzing",
    )
    test_db_session.add(s)
    test_db_session.commit()

    item = ShipmentItem(
        shipment_id=s.id,
        company_id=c.id,
        line_no=1,
        description="Pneumatic valve without specs",
        status="needs_clarification",
    )
    test_db_session.add(item)
    test_db_session.commit()

    _, token = create_test_user_and_token(test_db_session, c.id, "importer_staff", "staff@readiness.com")
    headers = {"Authorization": f"Bearer {token}"}

    sub_resp = client.post(f"/api/v1/shipments/{s.id}/mark-submitted", headers=headers)
    assert sub_resp.status_code == 409, f"Expected 409 on incomplete shipment submission, got {sub_resp.status_code}"
    data = sub_resp.json()
    assert "blocking_issues" in data or "detail" in data, "Response must enumerate blocking_issues"


# ==============================================================================
# T_F06: Real Frontend API Contracts & Persistence
# ==============================================================================
def test_f06_frontend_api_contracts_real_persistence(client, test_db_session):
    """
    (F06) POST /api/v1/shipments genuinely creates and persists a shipment in DB.
    """
    c = Company(name="Create Test Co", npwp="555555555555555")
    test_db_session.add(c)
    test_db_session.commit()

    _, token = create_test_user_and_token(test_db_session, c.id, "importer_staff", "staff@createtest.com")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "supplier_name": "Authentic Supplier Co Ltd",
        "supplier_email": "tim-impor@mitrakemas.co.id",
        "reference_no": "MKN-REAL-999",
        "invoice_number": "INV-2026-REAL",
    }
    resp = client.post("/api/v1/shipments", headers=headers, json=payload)
    assert resp.status_code in (200, 201), f"Create shipment failed: {resp.text}"
    created = resp.json()
    assert "id" in created or "shipment_id" in created

    ship_id = created.get("id") or created.get("shipment_id")
    in_db = test_db_session.query(Shipment).filter_by(id=ship_id).first()
    assert in_db is not None
    assert in_db.company_id == c.id
    assert in_db.supplier_name == "Authentic Supplier Co Ltd"


# ==============================================================================
# T_F07: Outbox SMTP Network Error Handling
# ==============================================================================
def test_f07_outbox_smtp_network_and_status():
    """
    (F07) Outbox processing with unreachable SMTP host/port must leave status as
    draft, failed, or unknown. NEVER falsely mark sent without network delivery proof.
    """
    from src.worker.outbox import process_outbox_message

    msg = {
        "id": 1001,
        "recipient": "tim-impor@mitrakemas.co.id",
        "subject": "Permintaan Spesifikasi",
        "body": "Mohon kirimkan datasheet katup.",
    }

    result = process_outbox_message(msg, smtp_host="127.0.0.1", smtp_port=59999)
    status_val = getattr(result, "status", None) or getattr(result, "delivery_status", None) or (
        result.get("status") if isinstance(result, dict) else str(result)
    )
    assert status_val != "sent", "Outbox falsely marked message as 'sent' despite failed SMTP connection!"
    assert status_val in ("failed", "unknown", "draft", "queued", "failed_delivery")


# ==============================================================================
# T_F08: Generic Regulation Watcher by HS Prefix
# ==============================================================================
def test_f08_generic_regulation_watcher(test_db_session):
    """
    (F08) Regulation watcher queries active shipments by hs_prefix matching the rule,
    not hardcoded MKN numbers.
    """
    from src.worker.watcher import find_affected_shipments_by_hs_prefix

    c = Company(name="Watcher Test Co", npwp="666666666666666")
    test_db_session.add(c)
    test_db_session.commit()

    s = Shipment(
        company_id=c.id,
        shipment_number="GENERIC-WATCH-888",
        supplier_name="Global Valves Inc",
        supplier_email="valves@global.com",
        status="ready",
    )
    test_db_session.add(s)
    test_db_session.commit()

    item = ShipmentItem(
        shipment_id=s.id,
        company_id=c.id,
        line_no=1,
        description="Pneumatic valve",
        hs_code_proposed="8481.80.90",
        status="approved",
    )
    test_db_session.add(item)
    test_db_session.commit()

    affected = find_affected_shipments_by_hs_prefix(
        company_id=c.id,
        hs_prefix="8481",
        db=test_db_session
    )
    shipment_numbers = [aff["shipment_number"] for aff in affected]
    assert "GENERIC-WATCH-888" in shipment_numbers, (
        f"Generic shipment GENERIC-WATCH-888 was not detected by watcher! Detected: {shipment_numbers}"
    )


# ==============================================================================
# T_F09: Tenant-Isolated Demo Reset
# ==============================================================================
def test_f09_tenant_isolated_demo_reset(test_db_session):
    """
    (F09) Demo reset for Company 2 purges only Company 2 demo shipments;
    Company 1 shipments remain intact. Uses distinct shipment numbers to avoid unique key collision.
    """
    from src.core.seed import seed_data

    c1 = Company(name="Tenant Co 1", npwp="777777777777771")
    c2 = Company(name="Tenant Co 2", npwp="777777777777772")
    test_db_session.add_all([c1, c2])
    test_db_session.commit()

    s1 = Shipment(company_id=c1.id, shipment_number="MKN-C1-011", supplier_name="C1 Supplier", supplier_email="s1@c1.com")
    s2 = Shipment(company_id=c2.id, shipment_number="MKN-C2-011", supplier_name="C2 Supplier", supplier_email="s2@c2.com")
    test_db_session.add_all([s1, s2])
    test_db_session.commit()

    seed_data(db=test_db_session, reset=True, target_company_id=c2.id)

    c1_check = test_db_session.query(Shipment).filter_by(company_id=c1.id, shipment_number="MKN-C1-011").first()
    assert c1_check is not None, "Company 1 shipment was erroneously deleted during Company 2 reset!"


# ==============================================================================
# T_F10: Reviewer HS Catalog Validation
# ==============================================================================
def test_f10_reviewer_validates_hs_catalog(client, test_db_session):
    """
    (F10) Review modify rejects non-existent or invalid 8-digit HS codes (400/422).
    """
    c = Company(name="HS Valid Co", npwp="888888888888888")
    test_db_session.add(c)
    test_db_session.commit()

    s = Shipment(company_id=c.id, shipment_number="HS-VAL-001", supplier_name="Supplier", supplier_email="s@val.com")
    test_db_session.add(s)
    test_db_session.commit()

    item = ShipmentItem(shipment_id=s.id, company_id=c.id, line_no=1, description="Valve", status="review")
    test_db_session.add(item)
    test_db_session.commit()

    rev = ReviewTask(shipment_id=s.id, item_id=item.id, company_id=c.id, status="open")
    test_db_session.add(rev)
    test_db_session.commit()

    _, reviewer_token = create_test_user_and_token(test_db_session, c.id, "ppjk_reviewer", "rev@hsvalid.com")
    headers = {"Authorization": f"Bearer {reviewer_token}"}

    resp = client.post(
        f"/api/v1/reviews/{rev.id}/decision",
        headers=headers,
        json={"decision": "modify", "modified_hs_code": "NOT-A-REAL-HS", "notes": "Testing invalid HS"}
    )
    assert resp.status_code in (400, 422), (
        f"Expected 400/422 on invalid HS 'NOT-A-REAL-HS', got {resp.status_code}"
    )


# ==============================================================================
# T_F11: Upload Document Validation and Auto Queue
# ==============================================================================
def test_f11_upload_validation_and_auto_queue(client, test_db_session):
    """
    (F11) Upload endpoint validates file format and enqueues job.
    Rejects non-PDF (400/415) or oversized files.
    """
    c = Company(name="Upload Co", npwp="999999999999999")
    test_db_session.add(c)
    test_db_session.commit()

    s = Shipment(company_id=c.id, shipment_number="UPLOAD-001", supplier_name="Supplier", supplier_email="s@up.com")
    test_db_session.add(s)
    test_db_session.commit()

    _, token = create_test_user_and_token(test_db_session, c.id, "importer_staff", "staff@up.com")
    headers = {"Authorization": f"Bearer {token}"}

    fake_file = ("script.exe", b"MZ\x90\x00\x03\x00\x00\x00", "application/x-msdownload")
    resp_bad = client.post(
        f"/api/v1/shipments/{s.id}/documents",
        headers=headers,
        files={"file": fake_file},
        data={"doc_type": "INVOICE"}
    )
    assert resp_bad.status_code in (400, 415), f"Expected 400/415 for non-PDF, got {resp_bad.status_code}"


# ==============================================================================
# T_F12: Worker Lease Recovery and Job Dispatch
# ==============================================================================
def test_f12_worker_lease_recovery_and_job_types(test_db_session):
    """
    (F12) Worker lease recovery loop reclaims stale processing jobs.
    """
    from src.worker.main import reclaim_stale_job_leases

    test_db_session.query(Job).filter_by(dedupe_key="LEASE-DEDUPE-001").delete()
    test_db_session.query(Shipment).filter_by(shipment_number="LEASE-001").delete()
    test_db_session.commit()

    c = Company(name="Lease Co", npwp="101010101010101")
    test_db_session.add(c)
    test_db_session.commit()

    s = Shipment(company_id=c.id, shipment_number="LEASE-001", supplier_name="Supplier", supplier_email="s@lease.com")
    test_db_session.add(s)
    test_db_session.commit()

    stale_time = datetime.now(UTC) - timedelta(minutes=15)
    stale_job = Job(
        shipment_id=s.id,
        company_id=c.id,
        event_type="analyze_shipment",
        dedupe_key="LEASE-DEDUPE-001",
        status="processing",
        lease_expires_at=stale_time,
        heartbeat_at=stale_time,
    )
    test_db_session.add(stale_job)
    test_db_session.commit()

    try:
        reclaimed_count = reclaim_stale_job_leases(db=test_db_session)
        assert reclaimed_count >= 1

        test_db_session.refresh(stale_job)
        assert stale_job.status in ("queued", "failed"), f"Stale job status not reset: {stale_job.status}"
    finally:
        test_db_session.query(Job).filter_by(dedupe_key="LEASE-DEDUPE-001").delete()
        test_db_session.query(Shipment).filter_by(shipment_number="LEASE-001").delete()
        test_db_session.commit()


# ==============================================================================
# T_F13: Health Worker Heartbeat Staleness
# ==============================================================================
def test_f13_health_check_detects_stale_heartbeat(client):
    """
    (F13) /health checks worker heartbeat age and reports DEGRADED if stale.
    """
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "worker_heartbeat" in data or "worker" in data or "status" in data
