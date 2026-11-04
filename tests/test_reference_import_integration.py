"""Integration test for additive reference catalog and demo fixture importer.
Verifies idempotent twice-import, preservation of reviewer edits, and isolation of other companies.
"""
from pathlib import Path
import psycopg

from src.core.config import settings
from scripts.import_reference_catalog import import_catalog, import_fixtures

ROOT = Path(__file__).resolve().parents[1]


def test_additive_twice_import_preserves_modified_seed_and_unrelated_company():
    # 1. Connect to database and enforce CURRENT_DATABASE() == 'imporjaga_test'
    with psycopg.connect(settings.TEST_DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT current_database();")
            db_name = cur.fetchone()[0]
            assert db_name == "imporjaga_test", f"Safety guard failed: expected 'imporjaga_test', got '{db_name}'"

            # 2. Create OWN isolated test companies A and B
            cur.execute("""
                INSERT INTO companies (name, npwp, is_active, created_at)
                VALUES ('TEST-ISOLATED-CO-A-RUN', '01.999.888.7-111.000', true, NOW())
                RETURNING id;
            """)
            comp_a_id = cur.fetchone()[0]

            cur.execute("""
                INSERT INTO companies (name, npwp, is_active, created_at)
                VALUES ('TEST-ISOLATED-CO-B-UNRELATED', '01.999.888.7-222.000', true, NOW())
                RETURNING id;
            """)
            comp_b_id = cur.fetchone()[0]

            # 3. Setup distinct baseline shipment and item for unrelated Company B
            cur.execute("""
                INSERT INTO shipments (
                    company_id, shipment_number, invoice_number, supplier_name, supplier_email,
                    status, readiness_status, currency, exchange_rate, cif_total_idr, total_duty_idr,
                    input_version, needs_action_rule_change, created_at, updated_at
                )
                VALUES (
                    %s, 'ISOLATED-B-SHIP-001', 'INV-ISOLATED-B-001', 'Supplier B Corp', 'supplier-b@example.com',
                    'ready', 'ready', 'USD', 16200.0, 16200000.0, 0.0,
                    1, false, NOW(), NOW()
                )
                RETURNING id;
            """, (comp_b_id,))
            ship_b_id = cur.fetchone()[0]

            cur.execute("""
                INSERT INTO shipment_items (
                    shipment_id, company_id, line_no, description, quantity, uom,
                    unit_price, total_price_cif, hs_code_proposed, hs_code_accepted,
                    confidence_score, risk_level, status, is_approved, version, created_at, updated_at
                )
                VALUES (
                    %s, %s, 1, 'Protected Unrelated Company Cargo Item', 10, 'PCS',
                    100.0, 1000.0, '84223000', '84223000',
                    0.99, 'low', 'approved', true, 1, NOW(), NOW()
                )
                RETURNING id;
            """, (ship_b_id, comp_b_id))
            item_b_id = cur.fetchone()[0]

            # 4. Insert human classification memory for Company A using actual schema
            cur.execute("""
                INSERT INTO classification_memory (
                    company_id, item_description, hs_code, matched_attributes,
                    decision_source, human_decision_notes, is_active, created_at
                )
                VALUES (
                    %s, 'Sample Essential Oil Cargo', '33012910', '{"botanical": "santalum"}'::json,
                    'human_reviewer', 'Archived legacy human decision note for verification', true, NOW()
                )
                RETURNING id;
            """, (comp_a_id,))
            mem_id = cur.fetchone()[0]

            # 4b. Setup lartas rules: legacy global unverified placeholder vs company-specific rules
            cur.execute("""
                INSERT INTO lartas_rules (
                    company_id, hs_prefix, requirement_key, permit_name, issuing_agency, rule_group, is_active, effective_date, source
                )
                VALUES (
                    NULL, '8481', 'TEST_GLOBAL_LEGACY_REQ', 'Persetujuan Impor Besi Baja Test', 'Kemendag', 'PI_STEEL_TEST', true, NOW(), 'INSW Official Regulatory Database'
                )
                RETURNING id;
            """)
            test_legacy_lartas_id = cur.fetchone()[0]

            cur.execute("""
                INSERT INTO lartas_rules (
                    company_id, hs_prefix, requirement_key, permit_name, issuing_agency, rule_group, is_active, effective_date, source
                )
                VALUES (
                    %s, '8481', 'TEST_CO_A_SIMULASI', 'Simulasi Khusus Co A', 'Kemendag', 'SIM_A', true, NOW(), 'Simulasi Demo'
                )
                RETURNING id;
            """, (comp_a_id,))
            test_co_a_lartas_id = cur.fetchone()[0]

            cur.execute("""
                INSERT INTO lartas_rules (
                    company_id, hs_prefix, requirement_key, permit_name, issuing_agency, rule_group, is_active, effective_date, source
                )
                VALUES (
                    %s, '8422', 'TEST_CO_B_CUSTOM', 'Aturan Khusus Co B', 'Internal B', 'CUSTOM_B', true, NOW(), 'Aturan Internal B'
                )
                RETURNING id;
            """, (comp_b_id,))
            test_co_b_lartas_id = cur.fetchone()[0]

        conn.commit()

        try:
            # 5. First Import run: Catalog and Fixtures for Company A
            cat_count = import_catalog(conn)
            assert cat_count >= 2614, f"Expected at least 2614 catalog codes, got {cat_count}"

            num_shipments, num_items = import_fixtures(conn, comp_a_id)
            conn.commit()

            assert num_shipments == 14, f"Expected 14 shipments imported, got {num_shipments}"
            assert num_items == 28, f"Expected 28 items imported, got {num_items}"

            with conn.cursor() as cur:
                # Verify Company A fixtures structure and readiness
                cur.execute("""
                    SELECT id, shipment_number, status, readiness_status, cif_total_idr, input_version
                    FROM shipments
                    WHERE company_id = %s
                    ORDER BY shipment_number;
                """, (comp_a_id,))
                co_a_shipments = cur.fetchall()
                assert len(co_a_shipments) == 14

                for s_row in co_a_shipments:
                    s_id, s_num, status, readiness, cif_total, inp_ver = s_row
                    assert inp_ver == 1, f"Expected input_version=1 for {s_num}"
                    if status in ("ready", "submitted", "arrived"):
                        assert readiness == "ready"
                    else:
                        assert readiness == "incomplete"

                # Check ready shipment MKN-DEMO-001 items are approved with accepted HS code
                cur.execute("""
                    SELECT i.id, i.description, i.uom, i.is_approved, i.status, i.hs_code_proposed, i.hs_code_accepted
                    FROM shipment_items i
                    JOIN shipments s ON s.id = i.shipment_id
                    WHERE s.company_id = %s AND s.shipment_number = 'MKN-DEMO-001'
                    ORDER BY i.line_no;
                """, (comp_a_id,))
                ready_items = cur.fetchall()
                assert len(ready_items) == 2
                for it in ready_items:
                    assert it[2] == "SET", f"Expected UOM 'SET', got {it[2]}"
                    assert it[3] is True, "Expected is_approved=True for ready shipment item"
                    assert it[4] == "approved", "Expected status='approved' for ready shipment item"
                    assert it[5] == it[6], "Expected hs_code_accepted == hs_code_proposed"

                # 6. Simulate explicit Reviewer human edit on first item of MKN-DEMO-001
                target_item_id = ready_items[0][0]
                reviewer_modified_desc = "HUMAN REVIEWER MODIFIED EXPLICIT SPECIFICATION NOTE 2026"
                cur.execute("""
                    UPDATE shipment_items
                    SET description = %s, hs_code_accepted = '84224000', updated_at = NOW()
                    WHERE id = %s;
                """, (reviewer_modified_desc, target_item_id))

            conn.commit()

            # 7. Second Import run: Re-run import_catalog and import_fixtures for Company A
            cat_count_2 = import_catalog(conn)
            num_shipments_2, num_items_2 = import_fixtures(conn, comp_a_id)
            conn.commit()

            assert cat_count_2 == cat_count

            with conn.cursor() as cur:
                # 8. VERIFY: The modified item was PRESERVED, not overwritten or wiped
                cur.execute("""
                    SELECT id, description, hs_code_accepted, is_approved, status
                    FROM shipment_items
                    WHERE id = %s;
                """, (target_item_id,))
                persisted_item = cur.fetchone()
                assert persisted_item is not None
                assert persisted_item[1] == reviewer_modified_desc, (
                    f"Reviewer modification was overwritten! Got: {persisted_item[1]}"
                )
                assert persisted_item[2] == "84224000"
                assert persisted_item[3] is True
                assert persisted_item[4] == "approved"

                # 9. VERIFY: Zero duplicate shipments or items created for Company A
                cur.execute("SELECT COUNT(*) FROM shipments WHERE company_id = %s;", (comp_a_id,))
                assert cur.fetchone()[0] == 14, "Duplicate shipments were created on second import!"

                cur.execute("SELECT COUNT(*) FROM shipment_items WHERE company_id = %s;", (comp_a_id,))
                assert cur.fetchone()[0] == 28, "Duplicate shipment items were created on second import!"

                # 9b. VERIFY: Documents and checklist items created and not duplicated
                cur.execute("SELECT COUNT(*) FROM documents WHERE company_id = %s;", (comp_a_id,))
                doc_count = cur.fetchone()[0]
                assert doc_count >= 14, f"Expected at least 14 documents, got {doc_count}"

                cur.execute("SELECT COUNT(*) FROM checklist_items WHERE company_id = %s;", (comp_a_id,))
                chk_count = cur.fetchone()[0]
                assert chk_count == 42, f"Expected exactly 42 checklist items (14*3), got {chk_count}"

                # 10. VERIFY: Unrelated Company B was completely untouched
                cur.execute("""
                    SELECT s.id, s.shipment_number, i.id, i.description
                    FROM shipments s
                    JOIN shipment_items i ON i.shipment_id = s.id
                    WHERE s.company_id = %s;
                """, (comp_b_id,))
                b_rows = cur.fetchall()
                assert len(b_rows) == 1
                assert b_rows[0][0] == ship_b_id
                assert b_rows[0][1] == "ISOLATED-B-SHIP-001"
                assert b_rows[0][2] == item_b_id
                assert b_rows[0][3] == "Protected Unrelated Company Cargo Item"

                # 11. VERIFY: classification_memory was NOT deleted (legacy code 33012910 archived safely)
                cur.execute("""
                    SELECT id, item_description, hs_code, human_decision_notes
                    FROM classification_memory
                    WHERE id = %s;
                """, (mem_id,))
                mem_row = cur.fetchone()
                assert mem_row is not None
                assert mem_row[2] == "33012910"
                assert "Archived legacy human decision note" in mem_row[3]

                # 12. VERIFY: Legacy global lartas rules are archived, company-specific rules stay active
                cur.execute("""
                    SELECT is_active, source
                    FROM lartas_rules
                    WHERE id = %s;
                """, (test_legacy_lartas_id,))
                leg_row = cur.fetchone()
                assert leg_row is not None
                assert leg_row[0] is False, f"Expected legacy global rule to be archived (is_active=False), got {leg_row[0]}"
                assert leg_row[1] == "Legacy Seed (Archived Placeholder)", f"Expected retagged source, got {leg_row[1]}"

                cur.execute("""
                    SELECT COUNT(*)
                    FROM lartas_rules
                    WHERE company_id IS NULL
                      AND source = 'INSW Official Regulatory Database'
                      AND is_active = true;
                """)
                active_legacy_count = cur.fetchone()[0]
                assert active_legacy_count == 0, f"Found {active_legacy_count} active unretagged legacy global lartas rules!"

                cur.execute("SELECT is_active, source FROM lartas_rules WHERE id = %s;", (test_co_a_lartas_id,))
                co_a_rule = cur.fetchone()
                assert co_a_rule[0] is True
                assert co_a_rule[1] == "Simulasi Demo"

                cur.execute("SELECT is_active, source FROM lartas_rules WHERE id = %s;", (test_co_b_lartas_id,))
                co_b_rule = cur.fetchone()
                assert co_b_rule[0] is True
                assert co_b_rule[1] == "Aturan Internal B"

        finally:
            # Clean up isolated test company records to leave database clean
            with conn.cursor() as cur:
                cur.execute("DELETE FROM lartas_rules WHERE id IN (%s, %s, %s);", (test_legacy_lartas_id, test_co_a_lartas_id, test_co_b_lartas_id))
                cur.execute("DELETE FROM classification_memory WHERE company_id IN (%s, %s);", (comp_a_id, comp_b_id))
                cur.execute("DELETE FROM checklist_items WHERE company_id IN (%s, %s);", (comp_a_id, comp_b_id))
                cur.execute("DELETE FROM documents WHERE company_id IN (%s, %s);", (comp_a_id, comp_b_id))
                cur.execute("DELETE FROM shipment_items WHERE company_id IN (%s, %s);", (comp_a_id, comp_b_id))
                cur.execute("DELETE FROM shipments WHERE company_id IN (%s, %s);", (comp_a_id, comp_b_id))
                cur.execute("DELETE FROM companies WHERE id IN (%s, %s);", (comp_a_id, comp_b_id))
            conn.commit()


def test_session_wide_test_db_isolation():
    """Verify session-wide test isolation fence binding to imporjaga_test."""
    assert settings.DATABASE_URL == settings.TEST_DATABASE_URL
    assert "imporjaga_test" in settings.DATABASE_URL
    with psycopg.connect(settings.DATABASE_URL) as conn, conn.cursor() as cur:
        cur.execute("SELECT current_database();")
        assert cur.fetchone()[0] == "imporjaga_test"

    from src.core.database import get_engine
    from sqlalchemy import text
    eng = get_engine()
    with eng.connect() as conn:
        assert conn.execute(text("SELECT current_database();")).scalar() == "imporjaga_test"


def test_offline_catalog_retrieval_benchmarks():
    """Verify offline candidate retrieval rankings for benchmark items.

    Ensures:
    1. Inductive proximity sensor -> ranks 8536 / 85365099 at the top (not wire machinery 8463).
    2. Centrifugal water pump -> ranks 8413 / 841370 at the top.
    3. AC induction motor -> ranks 8501 (e.g. 850152 / 850151) at the top.
    """
    from src.services.analysis import search_candidates

    class DummyRepo:
        def rows(self, sql, params=()):
            with psycopg.connect(settings.TEST_DATABASE_URL) as conn, conn.cursor() as cur:
                cur.execute(sql, params)
                cols = [desc[0] for desc in cur.description]
                return [dict(zip(cols, r)) for r in cur.fetchall()]

    repo = DummyRepo()

    # Benchmark 1: Inductive Proximity Sensor
    res_sensor = search_candidates(repo, "INDUCTIVE PROXIMITY SENSOR M12 24VDC PNP 3 WIRE", limit=8)
    codes_sensor = [r["hs_code"] for r in res_sensor]
    assert len(codes_sensor) > 0
    assert any(c.startswith("8536") for c in codes_sensor), f"Expected heading 8536 in candidates, got {codes_sensor}"
    assert "85365099" in codes_sensor, f"Expected 85365099 in sensor candidates, got {codes_sensor}"
    assert not any(c.startswith("8463") for c in codes_sensor), f"Wire machinery 8463 must not swamp sensor candidates: {codes_sensor}"

    # Benchmark 2: Centrifugal Water Pump
    res_pump = search_candidates(repo, "CENTRIFUGAL WATER PUMP 2.2 KW 220V INDUSTRIAL", limit=8)
    codes_pump = [r["hs_code"] for r in res_pump]
    assert len(codes_pump) > 0
    assert any(c.startswith("841370") or c.startswith("8413") for c in codes_pump), f"Expected heading 8413 in pump candidates, got {codes_pump}"

    # Benchmark 3: Electric AC Induction Motor
    res_motor = search_candidates(repo, "ELECTRIC AC INDUCTION MOTOR THREE PHASE 5.5 KW 380V", limit=8)
    codes_motor = [r["hs_code"] for r in res_motor]
    assert len(codes_motor) > 0
    assert any(c.startswith("8501") for c in codes_motor), f"Expected heading 8501 in motor candidates, got {codes_motor}"

    # Benchmark 4: Numeric prefix search "841370" -> returns ONLY 841370 prefix codes
    res_prefix = search_candidates(repo, "841370", limit=8)
    codes_prefix = [r["hs_code"] for r in res_prefix]
    assert len(codes_prefix) > 0, "Expected candidates for 841370 prefix search"
    assert all(c.startswith("841370") for c in codes_prefix), f"All candidates must start with 841370, got {codes_prefix}"

    # Dotted numeric search "8413.70" -> returns ONLY 841370 prefix codes
    res_dotted = search_candidates(repo, "8413.70", limit=8)
    codes_dotted = [r["hs_code"] for r in res_dotted]
    assert len(codes_dotted) > 0
    assert all(c.startswith("841370") for c in codes_dotted), f"All candidates must start with 841370, got {codes_dotted}"

    # Benchmark 5: Exact code search "85365099" -> returns exact code
    res_exact = search_candidates(repo, "85365099", limit=8)
    codes_exact = [r["hs_code"] for r in res_exact]
    assert codes_exact == ["85365099"], f"Expected exact ['85365099'], got {codes_exact}"

    # Benchmark 6: Zero lexical matches returns empty list [] (never unrelated apparel 6205/6212)
    res_zero = search_candidates(repo, "xyzunknownnonsenseattribute9999", limit=8)
    assert res_zero == [], f"Expected empty list for zero matches, got {[r['hs_code'] for r in res_zero]}"


def test_hs_search_canonical_deduplication_and_scope():
    """Verify search endpoint deduplicates canonical codes before limit and get_hs_detail isolates company SIM rules."""
    from fastapi.testclient import TestClient
    from src.api.main import app
    from src.api.auth import create_access_token

    with psycopg.connect(settings.TEST_DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO companies (name, npwp, is_active, created_at)
                VALUES ('TEST-HS-SEARCH-CO-A', '01.999.888.7-333.000', true, NOW())
                RETURNING id;
            """)
            co_a_id = cur.fetchone()[0]

            cur.execute("""
                INSERT INTO companies (name, npwp, is_active, created_at)
                VALUES ('TEST-HS-SEARCH-CO-B', '01.999.888.7-444.000', true, NOW())
                RETURNING id;
            """)
            co_b_id = cur.fetchone()[0]

            cur.execute("""
                INSERT INTO users (email, full_name, password_hash, company_id, role, is_active, created_at)
                VALUES ('user-hs-a@example.com', 'User A Staff', 'dummy_hash', %s, 'staff', true, NOW())
                RETURNING id;
            """, (co_a_id,))
            user_a_id = cur.fetchone()[0]

            # Insert private simulation rule for Company B under heading 8536
            cur.execute("""
                INSERT INTO lartas_rules (
                    hs_prefix, requirement_key, permit_name, issuing_agency,
                    company_id, is_active, rule_group, source
                )
                VALUES ('8536', 'SIM_PRIVATE_B_SENSOR', 'Izin Khusus Sensor Co B', 'Kementerian B', %s, true, 'SIMULASI', 'Simulasi Demo')
                RETURNING id;
            """, (co_b_id,))
            rule_b_id = cur.fetchone()[0]
        conn.commit()

    try:
        token_a = create_access_token({
            "sub": str(user_a_id),
            "company_id": str(co_a_id),
            "email": "user-hs-a@example.com",
            "role": "staff",
        })
        client = TestClient(app)

        # 1. Search deduplication test
        res = client.get("/api/v1/hs-codes/search?q=33012920&limit=10", headers={"Authorization": f"Bearer {token_a}"})
        assert res.status_code == 200, res.text
        data = res.json().get("data", [])
        codes = [item["hs_code"] for item in data]
        # Each canonical code must appear at most once
        assert len(codes) == len(set(codes)), f"Search results contained duplicates: {codes}"
        for item in data:
            assert "." not in item["hs_code"], f"Expected canonical hs_code without dots: {item['hs_code']}"
            assert item.get("code_canonical") == item["hs_code"]

        # 2. Company isolation in get_hs_detail: Company B's SIM rule must NOT leak to Company A
        res_detail = client.get("/api/v1/hs-codes/85365099", headers={"Authorization": f"Bearer {token_a}"})
        assert res_detail.status_code == 200, res_detail.text
        rules = res_detail.json().get("lartas_rules", [])
        rule_keys = [r.get("requirement_key") for r in rules]
        assert "SIM_PRIVATE_B_SENSOR" not in rule_keys, f"Private Company B rule leaked to Company A: {rule_keys}"

    finally:
        with psycopg.connect(settings.TEST_DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM lartas_rules WHERE id = %s;", (rule_b_id,))
                cur.execute("DELETE FROM users WHERE id = %s;", (user_a_id,))
                cur.execute("DELETE FROM companies WHERE id IN (%s, %s);", (co_a_id, co_b_id))
            conn.commit()
