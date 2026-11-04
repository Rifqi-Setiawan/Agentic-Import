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


def test_api_clarifications_and_answers():
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "staf@mitrakemas.co.id",
        "password": "imporjaga123"
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. List clarifications
    list_resp = client.get("/api/v1/clarifications", headers=headers)
    assert list_resp.status_code == 200
    clarifications = list_resp.json()["clarifications"]
    assert len(clarifications) > 0

    target = clarifications[0]
    # 2. Answer clarification
    ans_resp = client.post(
        f"/api/v1/clarifications/{target['id']}/answer",
        headers=headers,
        json={
            "answer": "Katup pneumatik tekanan kerja 12 bar dengan solenoid terintegrasi.",
            "answer_source": "staff_form",
        },
    )
    assert ans_resp.status_code == 202
    ans_data = ans_resp.json()
    assert ans_data["question_id"] == str(target["id"])
    assert ans_data["processing_status"] == "queued"
    assert ans_data["job_id"] is not None


def test_api_reviews_and_decisions():
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "reviewer@mitrakemas.co.id",
        "password": "imporjaga123"
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. List reviews
    list_resp = client.get("/api/v1/reviews", headers=headers)
    assert list_resp.status_code == 200
    reviews = list_resp.json()["reviews"]
    assert len(reviews) > 0

    target = reviews[0]
    # 2. Submit decision (approve)
    dec_resp = client.post(
        f"/api/v1/reviews/{target['id']}/decision",
        headers=headers,
        json={
            "decision": "approve",
            "notes": "Spesifikasi diverifikasi sesuai Bab 84.",
        },
    )
    assert dec_resp.status_code == 200
    dec_data = dec_resp.json()
    assert dec_data["status"] == "approve"
    assert dec_data["memory_recorded"] is True


def test_api_regulations_list():
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "staf@mitrakemas.co.id",
        "password": "imporjaga123"
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    list_resp = client.get("/api/v1/regulations", headers=headers)
    assert list_resp.status_code == 200
    regs = list_resp.json()["regulations"]
    assert len(regs) > 0
    assert "title" in regs[0]
    assert "regulation_number" in regs[0]


def test_api_shipment_extended_views():
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "staf@mitrakemas.co.id",
        "password": "imporjaga123"
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    shipments_resp = client.get("/api/v1/shipments", headers=headers)
    mkn11 = next(s for s in shipments_resp.json()["shipments"] if "011" in s["reference_no"])
    s_id = mkn11["id"]

    # 1. Items
    items_resp = client.get(f"/api/v1/shipments/{s_id}/items", headers=headers)
    assert items_resp.status_code == 200
    items = items_resp.json()["items"]
    assert len(items) == 5

    # 2. Documents
    docs_resp = client.get(f"/api/v1/shipments/{s_id}/documents", headers=headers)
    assert docs_resp.status_code == 200
    assert "documents" in docs_resp.json()

    # 3. Checklist
    chk_resp = client.get(f"/api/v1/shipments/{s_id}/checklist", headers=headers)
    assert chk_resp.status_code == 200
    assert "checklist" in chk_resp.json()

    # 4. PIB draft
    pib_resp = client.get(f"/api/v1/shipments/{s_id}/pib-draft", headers=headers)
    assert pib_resp.status_code == 200
    pib = pib_resp.json()["pib_draft"]
    assert pib["shipment_number"] == "MKN-011"

    # 5. Messages
    msg_resp = client.get(f"/api/v1/shipments/{s_id}/messages", headers=headers)
    assert msg_resp.status_code == 200
    assert "messages" in msg_resp.json()

    # 6. Trigger analysis
    analyze_resp = client.post(f"/api/v1/shipments/{s_id}/analyze", headers=headers)
    assert analyze_resp.status_code == 200
    assert analyze_resp.json()["status"] in ("queued", "already_running")


def test_api_admin_demo_reset():
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "admin@mitrakemas.co.id",
        "password": "imporjaga123"
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    reset_resp = client.post("/api/v1/admin/demo/reset", headers=headers)
    assert reset_resp.status_code == 200
    assert reset_resp.json()["status"] == "success"

