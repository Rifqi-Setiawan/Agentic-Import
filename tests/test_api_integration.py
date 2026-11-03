from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def test_api_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "UP"
    assert data["database"] == "connected"


def test_api_login_and_access_flow():
    # 1. Login with Staff Account
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "staf@mitrakemas.co.id",
        "password": "imporjaga123"
    })
    assert login_resp.status_code == 200
    login_data = login_resp.json()
    token = login_data["access_token"]
    assert token is not None
    assert login_data["role"] in ("staf", "importer_staff")
    assert login_data["company_name"] == "PT Mitra Kemas Nusantara"

    headers = {"Authorization": f"Bearer {token}"}

    # 2. Get Me
    me_resp = client.get("/api/v1/auth/me", headers=headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "staf@mitrakemas.co.id"

    # 3. List Shipments
    shipments_resp = client.get("/api/v1/shipments", headers=headers)
    assert shipments_resp.status_code == 200
    shipments = shipments_resp.json()["shipments"]
    assert len(shipments) >= 4
    ref_numbers = [s["reference_no"] for s in shipments]
    assert any("011" in r for r in ref_numbers)
    assert any("007" in r for r in ref_numbers)
    assert any("008" in r for r in ref_numbers)
    assert any("003" in r for r in ref_numbers)

    # 4. Detail MKN-011
    mkn11 = next(s for s in shipments if "011" in s["reference_no"])
    detail_resp = client.get(f"/api/v1/shipments/{mkn11['id']}", headers=headers)
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert "011" in detail["reference_no"]
    assert detail["readiness_status"] in ("incomplete", "blocked")
    assert detail["is_ready"] is False
    assert len(detail["items"]) == 5
    assert len(detail["blocking_issues"]) > 0

    # 6. Test HS Search
    hs_resp = client.get("/api/v1/hs-codes/search?q=katup", headers=headers)
    assert hs_resp.status_code == 200
    assert len(hs_resp.json()["data"]) > 0


def test_api_regulation_simulation():
    # Login as Admin
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "admin@mitrakemas.co.id",
        "password": "imporjaga123"
    })
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Trigger simulation for heading 8481
    sim_resp = client.post("/api/v1/regulations/simulate-demo", headers=headers, json={
        "hs_prefix": "8481",
        "requirement_code": "LS_NEW_2026",
        "title": "Permendag No. 99/2026 — Verifikasi Katup & Valve"
    })
    assert sim_resp.status_code == 200
    sim_data = sim_resp.json()
    assert sim_data["status"] == "success"
    assert sim_data["affected_prefix"] == "8481"
