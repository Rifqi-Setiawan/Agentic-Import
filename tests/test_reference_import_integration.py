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
