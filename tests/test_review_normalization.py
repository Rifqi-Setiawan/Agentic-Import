"""Regression for human-entered dotted BTKI codes crossing into duty calculation."""
from fastapi.testclient import TestClient

from src.api.deps import get_current_user, get_db_cursor
from src.api.main import app
from tests.test_audit_api_regressions import ScenarioCursor, forbid_real_database  # noqa: F401


def test_dotted_review_code_is_persisted_in_pipeline_canonical_format():
    class CatalogCursor(ScenarioCursor):
        def execute(self, query, params=None):
            result = super().execute(query, params)
            if "from hs_codes" in str(query).lower():
                self.rows = [("8481.80.99",)]
            return result

    cur = CatalogCursor("review")
    app.dependency_overrides[get_current_user] = lambda: {
        "id": "1", "company_id": "1", "email": "qa@example.invalid", "role": "ppjk_reviewer",
    }
    app.dependency_overrides[get_db_cursor] = lambda: cur
    result = TestClient(app).post("/api/v1/reviews/7/decision", json={
        "decision": "modify", "modified_hs_code": "8481.80.99", "notes": "Fictional QA",
    })
    assert result.status_code == 200, result.text
    assert result.json()["hs_code"] == "84818099"
    writes = [params for sql, params in cur.executed if sql.startswith("update shipment_items")]
    assert writes[0][0] == "84818099"
