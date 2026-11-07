from contextlib import contextmanager
from datetime import UTC, datetime
from decimal import Decimal
import json
from uuid import uuid4

import psycopg
import pytest
from fastapi.testclient import TestClient
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from src.api.deps import get_current_user, get_db_cursor
from src.api.main import app
from src.agent.graph import build_analysis_graph
from src.core.config import settings
from src.core.import_rates import pph22_rate
from src.domain.duty import DutyInput, calculate_import_duties
from src.services import analysis
from src.services.analysis_repository import AnalysisRepository
from src.worker import main as worker
from src.worker.outbox import OutboxStatus


@pytest.fixture
def workspace(monkeypatch):
    with psycopg.connect(settings.TEST_DATABASE_URL) as db:
        company_id = db.execute(
            "INSERT INTO companies (name,is_active) VALUES (%s,true) RETURNING id",
            ("Repair test " + uuid4().hex,),
        ).fetchone()[0]

        def cursor():
            with db.cursor() as cur:
                yield cur

        monkeypatch.setitem(app.dependency_overrides, get_db_cursor, cursor)
        monkeypatch.setitem(app.dependency_overrides, get_current_user,
                            lambda: {"company_id": str(company_id), "role": "admin"})
        try:
            yield db, company_id, TestClient(app)
        finally:
            db.rollback()


def create_shipment(db, company_id, reference, status):
    return db.execute("""INSERT INTO shipments
        (company_id,shipment_number,supplier_name,supplier_email,status,readiness_status,input_version)
        VALUES (%s,%s,'Supplier test','test@example.test',%s,'ready',1) RETURNING id""",
        (company_id, reference, status)).fetchone()[0]


def graph_in_transaction(db, company_id, shipment_id, run_id, monkeypatch):
    class Transaction:
        def execute(self, *args):
            return db.execute(*args)

        def commit(self):
            pass

    @contextmanager
    def connect(state):
        yield AnalysisRepository(Transaction(), company_id, shipment_id, run_id)

    monkeypatch.setattr(analysis, "connect", connect)
    db.row_factory = dict_row
    return build_analysis_graph()


def test_regulation_queues_and_recalculates_matching_active_shipments_once(workspace, monkeypatch):
    db, company_id, client = workspace
    shipments = {}
    for state in ("ready", "submitted", "arrived", "unrelated"):
        reference = uuid4().hex
        shipment_id = create_shipment(db, company_id, reference, "ready" if state == "unrelated" else state)
        shipments[state] = (shipment_id, reference)
        db.execute("""INSERT INTO shipment_items (shipment_id,company_id,line_no,description,hs_code_accepted)
            VALUES (%s,%s,1,'Test item',%s)""",
            (shipment_id, company_id, "84223000" if state == "unrelated" else "8481.80.99"))

    for _ in range(2):
        response = client.post("/api/v1/regulations/simulate-demo", json={"hs_prefix": "8481"})
        assert response.status_code == 200
        assert set(response.json()["affected_shipments"]) == {shipments["ready"][1], shipments["submitted"][1]}
    jobs = db.execute("SELECT shipment_id,event_type,payload FROM jobs WHERE company_id=%s", (company_id,)).fetchall()
    assert {row[0] for row in jobs} == {shipments["ready"][0], shipments["submitted"][0]}
    assert len(jobs) == 2
    assert all(row[1] == "new_rule" and row[2]["mode"] == "recalc_only" for row in jobs)
    assert db.execute("SELECT status,needs_action_rule_change FROM shipments WHERE id=%s",
                      (shipments["submitted"][0],)).fetchone() == ("submitted", True)
    shipment_id = shipments["ready"][0]
    db.execute("UPDATE shipment_items SET is_approved=true,status='approved' WHERE shipment_id=%s", (shipment_id,))
    db.execute("""INSERT INTO hs_codes (hs_code,description_id,lartas_coverage)
        VALUES ('84818099','Katup','unknown') ON CONFLICT (hs_code) DO NOTHING""")
    run_id = db.execute("""INSERT INTO agent_runs (company_id,shipment_id,status)
        VALUES (%s,%s,'running') RETURNING id""", (company_id, shipment_id)).fetchone()[0]

    result = graph_in_transaction(db, company_id, shipment_id, run_id, monkeypatch).invoke({
        "company_id": str(company_id), "shipment_id": str(shipment_id), "run_id": str(run_id),
        "mode": "recalc_only", "event_type": "new_rule",
    })
    assert result["outcome"] == "action_required"
    assert db.execute("""SELECT status FROM checklist_items WHERE shipment_id=%s
        AND requirement_code='LS_NEW_2026'""", (shipment_id,)).fetchone()["status"] == "missing"
    assert db.execute("""SELECT hs_code_accepted FROM shipment_items WHERE shipment_id=%s""",
                      (shipment_id,)).fetchone()["hs_code_accepted"] == "8481.80.99"


@pytest.mark.parametrize(("mode", "item_count"), [("assist", 8), ("auto", 1)])
def test_graph_applies_item_budget_memory_and_approval_policy(workspace, monkeypatch, mode, item_count):
    db, company_id, _ = workspace
    shipment_id = create_shipment(db, company_id, uuid4().hex, "draft")
    run_id = db.execute("""INSERT INTO agent_runs (company_id,shipment_id,status,total_tokens)
        VALUES (%s,%s,'running',0) RETURNING id""", (company_id, shipment_id)).fetchone()[0]
    db.execute("UPDATE companies SET autonomy_level=%s,has_api=true WHERE id=%s", (mode, company_id))
    db.execute("""INSERT INTO hs_codes (hs_code,description_id,lartas_coverage,bm_rate,source)
        VALUES ('85365099','Sakelar lainnya','verified_none',5,'BTKI 2022')
        ON CONFLICT (hs_code) DO UPDATE SET lartas_coverage='verified_none',bm_rate=5""")
    description = "Sakelar sensor proximity teruji"
    db.execute("""INSERT INTO classification_memory
        (company_id,item_description,hs_code,decision_source,is_active)
        VALUES (%s,%s,'85365099','human_review',true)""", (company_id, description))
    db.execute("UPDATE shipments SET currency='IDR' WHERE id=%s", (shipment_id,))
    item_ids = [
        db.execute("""INSERT INTO shipment_items
            (shipment_id,company_id,line_no,description,total_price_cif,is_approved)
            VALUES (%s,%s,%s,%s,78940712.50,false) RETURNING id""",
            (shipment_id, company_id, line, description)).fetchone()[0]
        for line in range(1, item_count + 1)
    ]
    classification_calls = 0

    def model(messages, **options):
        nonlocal classification_calls
        system = messages[0]["content"]
        if options.get("tools"):
            classification_calls += 1
            data = json.loads(messages[1]["content"])
            assert data["approved_memory"][0]["hs_code"] == "85365099"
            args = {"hs_code": "85365099", "quote": "Sakelar lainnya", "confidence": .97,
                    "alternatives": [], "rationale": "Fungsi barang adalah sakelar kedekatan untuk sirkuit listrik."}
            calls = [{"id": "classification", "function": {"name": "submit_classification", "arguments": json.dumps(args)}}]
            tokens = 12001 if mode == "assist" and classification_calls == 1 else 500
            return {"total_tokens": tokens, "message": {"tool_calls": calls}}
        if system.startswith("Susun"):
            content = {"order": list(reversed(item_ids)), "summary": "Urutan klasifikasi"}
        elif system.startswith("Periksa"):
            content = {"findings": [], "summary": "Pemeriksaan selesai"}
        else:
            content = {"supplier_document_ids": []}
        return {"content": json.dumps(content), "total_tokens": 50}

    monkeypatch.setattr(analysis, "call_llm", model)
    result = graph_in_transaction(db, company_id, shipment_id, run_id, monkeypatch).invoke({
        "company_id": str(company_id), "shipment_id": str(shipment_id), "run_id": str(run_id), "mode": "auto",
    })
    assert classification_calls == item_count
    if mode == "auto":
        review_notes = db.execute("SELECT notes FROM review_tasks WHERE shipment_id=%s", (shipment_id,)).fetchall()
        assert result["items"][0]["approval_origin"] == "auto_rule_gate", review_notes
        assert result["items"][0]["hs_code_accepted"] == "85365099"
        assert db.execute("""SELECT total_duties_idr FROM duty_calculations WHERE shipment_id=%s AND is_current""",
                          (shipment_id,)).fetchone()["total_duties_idr"] == 15139000
    else:
        assert result["items"][-1]["status"] == "needs_review"
        assert all(item["status"] == "classified" for item in result["items"][:-1])
        assert not any(item["is_approved"] for item in result["items"])


def test_shipment_run_history_uses_started_at(workspace):
    db, company_id, client = workspace
    shipment_id = create_shipment(db, company_id, uuid4().hex, "draft")
    started = datetime.now(UTC)
    db.execute("""INSERT INTO agent_runs (shipment_id,company_id,status,started_at)
        VALUES (%s,%s,'succeeded',%s)""", (shipment_id, company_id, started))
    response = client.get(f"/api/v1/shipments/{shipment_id}/runs")
    assert response.status_code == 200
    (run,) = response.json()["runs"]
    assert datetime.fromisoformat(run["created_at"]) == started
    assert run["created_at"] == run["started_at"]


def test_reminder_delivery_uses_separate_dedupe_key(workspace, monkeypatch):
    db, company_id, _ = workspace
    shipment_id = create_shipment(db, company_id, uuid4().hex, "needs_clarification")
    item_id = db.execute("""INSERT INTO shipment_items (shipment_id,company_id,line_no,description)
        VALUES (%s,%s,1,'Test item') RETURNING id""", (shipment_id, company_id)).fetchone()[0]
    db.execute("""INSERT INTO clarifications (shipment_id,company_id,item_id,question,status)
        VALUES (%s,%s,%s,'Spesifikasi?', 'open')""", (shipment_id, company_id, item_id))
    key = uuid4().hex
    message_id = db.execute("""INSERT INTO messages
        (shipment_id,company_id,dedupe_key,recipient,subject,body,delivery_status)
        VALUES (%s,%s,%s,'test@example.test','Pertanyaan','Spesifikasi?', 'pending') RETURNING id""",
        (shipment_id, company_id, key)).fetchone()[0]

    class Sent:
        delivery_status = OutboxStatus.SENT

    monkeypatch.setattr(worker, "process_outbox_message", lambda message: Sent())
    db.row_factory = dict_row
    worker.deliver(db, {"shipment_id": shipment_id, "company_id": company_id,
                        "payload": {"message_id": message_id}})
    followup = db.execute("SELECT * FROM jobs WHERE dedupe_key=%s", ("followup:" + key,)).fetchone()
    assert followup
    # A legacy follow-up key is occupied even after that old job has completed.
    db.execute("""INSERT INTO jobs (shipment_id,company_id,dedupe_key,event_type,payload,status)
        VALUES (%s,%s,%s,'followup',%s,'completed')""",
        (shipment_id, company_id, "reminder:" + key, Jsonb({"message_id": message_id})))
    worker.followup(db, followup)
    worker.followup(db, followup)
    reminder = db.execute("SELECT * FROM jobs WHERE dedupe_key=%s", ("mail-reminder:" + key,)).fetchone()
    assert reminder and reminder["event_type"] == "send_email"
    worker.deliver(db, reminder)
    assert db.execute("SELECT delivery_status FROM messages WHERE dedupe_key=%s",
                      ("reminder:" + key,)).fetchone()["delivery_status"] == "sent"


def test_demo_reset_reloads_only_configured_workspace(workspace, monkeypatch):
    db, company_id, client = workspace
    monkeypatch.setattr(settings, "DEMO_COMPANY_ID", company_id)
    other = db.execute("INSERT INTO companies (name) VALUES ('Other test') RETURNING id").fetchone()[0]
    other_id = create_shipment(db, other, uuid4().hex, "ready")
    old_id = create_shipment(db, company_id, uuid4().hex, "draft")
    response = client.post("/api/v1/admin/demo/reset")
    assert response.status_code == 200
    assert db.execute("SELECT COUNT(*) FROM shipments WHERE company_id=%s", (company_id,)).fetchone() == (15,)
    assert db.execute("SELECT id FROM shipments WHERE id=%s", (old_id,)).fetchone() is None
    assert db.execute("SELECT id FROM shipments WHERE id=%s", (other_id,)).fetchone() == (other_id,)


@pytest.mark.parametrize(("has_api", "expected_pph", "expected_total"), [
    (True, 2073000, 15139000), (False, 6217000, 19283000),
])
def test_prd_estimate_uses_importer_api_status(has_api, expected_pph, expected_total):
    rate, _ = pph22_rate(has_api)
    result = calculate_import_duties(DutyInput(cif_idr=Decimal("78940712.50"), pph_percentage=rate))
    assert result.bm_idr == 3948000
    assert result.ppn_idr == 9118000
    assert result.pph_idr == expected_pph
    assert result.total_duties_idr == expected_total
