"""Independent audit regressions, authored before remediation.

No real database is allowed. Run from candidate repository root:
  PYTHONPATH=. .venv/bin/python -m pytest /path/test_audit_api_regressions.py -v

These black-box HTTP checks cover the audited controller boundaries. They do not
replace PostgreSQL/worker/SMTP E2E acceptance. ScenarioCursor deliberately fails
on unknown SQL so a refactor cannot silently pass against made-up state.
"""
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.api.deps import get_current_user, get_db_cursor


class ScenarioCursor:
    def __init__(self, scenario):
        self.scenario = scenario
        self.rows = []
        self.executed = []

    def execute(self, query, params=None):
        q = " ".join(str(query).lower().split())
        self.executed.append((q, params))
        self.rows = []
        now = datetime.now(timezone.utc)
        if self.scenario == "foreign_pib":
            if "from shipments" in q:
                # A company-scoped read must not return the foreign fixture.
                if "company_id" in q.split(" where ", 1)[-1]:
                    self.rows = []
                else:
                    self.rows = [(99, "FOREIGN-99", "Foreign supplier", "USD", "ready", "ready", "Foreign importer", "FOREIGN-NPWP")]
            elif "from duty_calculations" in q:
                self.rows = []
            else:
                raise AssertionError(f"Unmodelled SQL in foreign PIB test: {q}")
        elif self.scenario == "unapproved_no_documents":
            if "from shipments" in q:
                self.rows = [(1, "draft")]
            elif "from documents" in q or "from clarifications" in q:
                self.rows = []
            elif "from shipment_items" in q:
                self.rows = [("classified",)]
            elif "update shipments" in q:
                self.rows = [(11, "submitted", now)]
            elif "from review_tasks" in q:
                self.rows = [(1,)]  # outstanding review exists
            elif "from checklist_items" in q:
                self.rows = [("INVOICE", "missing")]
            elif "from jobs" in q:
                self.rows = []
            else:
                raise AssertionError(f"Unmodelled SQL in readiness test: {q}")
        elif self.scenario in ("review", "unknown_hs"):
            if "from review_tasks" in q:
                self.rows = [(7, 1, 11, 44, "open", "Industrial valve", None, "84818099")]
            elif "from hs_codes" in q:
                self.rows = []
            elif q.startswith("update ") or q.startswith("insert "):
                self.rows = [(1,)]
            else:
                raise AssertionError(f"Unmodelled SQL in review test: {q}")
        elif self.scenario == "upload":
            if "from shipments" in q:
                self.rows = [(1, 1)]
            elif q.startswith("insert into documents"):
                self.rows = [(123,)]
            elif "count(" in q:
                self.rows = [(0,)]
            else:
                raise AssertionError(f"Unmodelled SQL in upload test: {q}")
        elif self.scenario == "reset":
            if "count(" in q:
                self.rows = [(0,)]
            else:
                raise AssertionError(f"Unmodelled SQL in reset test: {q}")
        else:
            raise AssertionError(f"Unknown fixture {self.scenario}")
        return self

    def fetchone(self):
        return self.rows.pop(0) if self.rows else None

    def fetchall(self):
        rows, self.rows = self.rows, []
        return rows


@pytest.fixture(autouse=True)
def forbid_real_database(monkeypatch):
    import psycopg
    from sqlalchemy.engine import Engine

    def denied(*args, **kwargs):
        raise AssertionError("AUDIT TEST SAFETY: real database access forbidden")
    monkeypatch.setattr(psycopg, "connect", denied)
    monkeypatch.setattr(Engine, "connect", denied)
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client_for():
    def make(scenario, role="importer_staff"):
        cur = ScenarioCursor(scenario)
        app.dependency_overrides[get_current_user] = lambda: {
            "id": "1", "company_id": "1", "email": "audit@example.invalid", "role": role,
        }
        app.dependency_overrides[get_db_cursor] = lambda: cur
        return TestClient(app, raise_server_exceptions=True), cur
    return make


def test_foreign_company_pib_returns_404(client_for):
    client, _ = client_for("foreign_pib")
    response = client.get("/api/v1/shipments/99/pib-draft")
    assert response.status_code == 404, "Foreign importer identity/NPWP must never be returned"


def test_staff_cannot_decide_reviewer_task(client_for):
    client, cur = client_for("review")
    response = client.post("/api/v1/reviews/7/decision", json={"decision": "approve", "notes": "audit"})
    assert response.status_code == 403, "Staff is not a reviewer"
    assert not any(q.startswith(("insert ", "update ")) for q, _ in cur.executed)


def test_staff_cannot_reset_demo(client_for, monkeypatch):
    import src.api.admin_routes as routes
    called = []
    monkeypatch.setattr(routes, "seed_data", lambda **kw: called.append(kw))
    client, _ = client_for("reset")
    response = client.post("/api/v1/admin/demo/reset")
    assert response.status_code == 403, "Reset is admin-only"
    assert called == [], "Unauthorized reset must not call seed or touch tenant data"


def test_unapproved_item_and_missing_documents_cannot_submit(client_for):
    client, cur = client_for("unapproved_no_documents")
    response = client.post("/api/v1/shipments/11/mark-submitted")
    assert response.status_code == 409, "Classified != approved; zero uploaded documents != complete requirements"
    assert not any("update shipments" in q for q, _ in cur.executed)


@pytest.mark.parametrize("bad_code", ["NOT-A-REAL-HS", "123", "99999999"])
def test_review_modify_rejects_invalid_or_unknown_hs(client_for, bad_code):
    client, cur = client_for("unknown_hs", role="ppjk_reviewer")
    response = client.post("/api/v1/reviews/7/decision", json={
        "decision": "modify", "modified_hs_code": bad_code, "notes": "audit",
    })
    assert response.status_code in (400, 404, 422), "Format and catalogue membership both must be validated"
    assert not any("insert into classification_memory" in q for q, _ in cur.executed)


def test_non_pdf_upload_rejected_before_provided(client_for, monkeypatch, tmp_path):
    from src.core.config import settings
    monkeypatch.setattr(settings, "STORAGE_VAULT_PATH", str(tmp_path))
    client, cur = client_for("upload")
    response = client.post("/api/v1/shipments/11/documents", data={"doc_type": "invoice"}, files={
        "file": ("invoice.pdf", b"this is not a PDF", "application/pdf"),
    })
    assert response.status_code in (400, 415, 422), "Filename and MIME alone do not prove a PDF"
    assert not any("insert into documents" in q for q, _ in cur.executed), "Unvalidated bytes must not become provided evidence"

