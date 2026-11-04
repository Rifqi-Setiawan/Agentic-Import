"""Detail must never label an approved item ready while requirements are missing."""
from datetime import UTC, datetime

from fastapi.testclient import TestClient

from src.api.deps import get_current_user, get_db_cursor
from src.api.main import app
from tests.test_audit_api_regressions import forbid_real_database  # noqa: F401


def test_detail_includes_missing_requirements_reviews_and_active_analysis():
    now = datetime.now(UTC)

    class DetailCursor:
        rows = []

        def execute(self, sql, params=None):
            q = " ".join(sql.lower().split())
            self.rows = []
            if "from shipments s" in q:
                self.rows = [(1, 1, "QA", "QA", "Fictional", "qa@example.invalid", "IDR", 100,
                    "needs_documents", "incomplete", 1, None, None, now)]
            elif "from shipment_items i" in q:
                self.rows = [(1, 1, "Sensor", 1, "PCS", 100, 100, "approved", "85437090", None, True)]
            elif "from documents d" in q:
                self.rows = [(1, "INVOICE", "qa.pdf", 100, "provided", now)]
            elif "from checklist_items" in q:
                self.rows = [("Packing list", "missing"), ("B/L", "missing")]
            elif "from review_tasks" in q or "from jobs" in q:
                self.rows = [(1,)]
            elif any(table in q for table in ("from agent_runs", "from agent_steps", "from clarifications")):
                pass
            else:
                raise AssertionError(q)

        def fetchone(self):
            return self.rows.pop(0) if self.rows else None

        def fetchall(self):
            result, self.rows = self.rows, []
            return result

    app.dependency_overrides[get_current_user] = lambda: {"id": "1", "company_id": "1", "role": "importer_staff"}
    app.dependency_overrides[get_db_cursor] = lambda: DetailCursor()
    response = TestClient(app).get("/api/v1/shipments/1")
    assert response.status_code == 200, response.text
    detail = response.json()
    assert detail["readiness_status"] == "incomplete"
    assert detail["is_ready"] is False
    assert detail["pending_job_count"] == 1
    assert any("Packing list" in issue for issue in detail["blocking_issues"])
    assert any("review" in issue for issue in detail["blocking_issues"])
