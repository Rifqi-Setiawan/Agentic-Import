import argparse
import json
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import psycopg
from src.core.config import settings

CATALOG_FILE = ROOT / "data" / "reference" / "hs_codes_btki2022.json"
FIXTURES_FILE = ROOT / "data" / "demo" / "shipments.json"
DOCS_DIR = ROOT / "data" / "demo" / "documents"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Additive idempotent importer for BTKI 2022 reference catalog and demo fixtures."
    )
    parser.add_argument(
        "--company-id",
        type=int,
        required=True,
        help="Target company ID (required, no fallback)",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        default=False,
        help="Target live/production database (Parent authorization required; worker must never use this)",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        default=False,
        help="Apply changes to live database (must accompany --live)",
    )
    parser.add_argument(
        "--db-url",
        type=str,
        default=None,
        help="Explicit database URL override (optional)",
    )
    return parser.parse_args()


def get_connection(db_url: str | None, is_live: bool, is_apply: bool):
    """
    Connect to database with safety guards:
    - If --live AND --apply are both explicitly set: connects to settings.DATABASE_URL (Parent authorized only).
    - Otherwise: defaults strictly to settings.TEST_DATABASE_URL and verifies current_database() == 'imporjaga_test'.
    """
    if is_live and is_apply:
        url = db_url or settings.DATABASE_URL
        conn = psycopg.connect(url, autocommit=False)
        with conn.cursor() as cur:
            cur.execute("SELECT current_database();")
            db_name = cur.fetchone()[0]
            if db_name != "imporjaga":
                conn.close()
                raise RuntimeError(
                    f"LIVE DB GUARD: Connected to '{db_name}', expected EXACT 'imporjaga'. "
                    "Aborting live deployment."
                )
        print(f"AUTHORIZED LIVE DEPLOYMENT MODE: Target database is '{db_name}'")
        return conn, db_name
    elif is_live and not is_apply:
        raise ValueError("Live mode requires explicit --apply flag: both --live and --apply are mandatory for production apply.")
    else:
        url = db_url or settings.TEST_DATABASE_URL
        conn = psycopg.connect(url, autocommit=False)
        with conn.cursor() as cur:
            cur.execute("SELECT current_database();")
            db_name = cur.fetchone()[0]
            if db_name != "imporjaga_test":
                conn.close()
                raise RuntimeError(
                    f"TEST DB GUARD: Connected to '{db_name}', expected 'imporjaga_test'. "
                    "Refusing execution without authorized --live --apply flags."
                )
        print(f"TEST MODE: Connected to verified test database: '{db_name}'")
        return conn, db_name


def import_catalog(conn):
    """
    Additive catalog sync:
    - Reads 2,614 official BTKI 2022 codes.
    - Updates descriptions for canonical and dotted variants.
    - Inserts missing canonical codes with honest unknown rates (NULL).
    - NO DELETE of hs_codes or classification_memory (legacy codes remain archived/unservable via catalog guard).
    """
    if not CATALOG_FILE.exists():
        raise FileNotFoundError(f"Reference catalog file not found: {CATALOG_FILE}")

    with open(CATALOG_FILE, encoding="utf-8") as f:
        catalog = json.load(f)

    codes = catalog.get("codes", [])
    print(f"Loaded {len(codes)} official BTKI 2022 codes from {CATALOG_FILE}")

    with conn.cursor() as cur:
        inserted = 0
        updated = 0

        for item in codes:
            code = item["code"]
            desc_id = item["description_id"]
            desc_en = item["description_en"]
            source = "BTKI 2022 DJBC"

            # Update existing records (including dotted variants) so descriptions are canonical
            # and unverified legacy rates are cleared to NULL, lartas_coverage to 'unknown'
            cur.execute("""
                UPDATE hs_codes
                SET description_id = %s,
                    description_en = %s,
                    bm_rate = NULL,
                    ppn_rate = NULL,
                    pph_rate = NULL,
                    lartas_coverage = 'unknown',
                    source = %s,
                    last_checked_at = NOW()
                WHERE replace(hs_code, '.', '') = %s;
            """, (desc_id, desc_en, source, code))

            # Check if canonical un-dotted code exists
            cur.execute("SELECT id FROM hs_codes WHERE hs_code = %s;", (code,))
            existing = cur.fetchone()

            if existing:
                updated += 1
            else:
                cur.execute("""
                    INSERT INTO hs_codes (
                        hs_code, description_id, description_en, bm_rate, ppn_rate, pph_rate,
                        lartas_coverage, source, last_checked_at
                    )
                    VALUES (%s, %s, %s, NULL, NULL, NULL, 'unknown', %s, NOW());
                """, (code, desc_id, desc_en, source))
                inserted += 1

    print(f"Catalog sync complete: {inserted} inserted, {updated} updated (total {len(codes)} official codes).")
    return len(codes)


def import_fixtures(conn, company_id: int):
    """
    Additive fixture import:
    - Scoped strictly to company_id.
    - If shipment scenario already exists for company_id: skip entirely to preserve lifecycle status and reviewer edits!
    - Only inserts untouched missing shipments and items.
    - NO DELETE of shipment_items or classification_memory.
    - Uses existing model columns only (no raw rationale column in shipment_items).
    - For ready fixtures: sets items as is_approved=True, status='approved', hs_code_accepted=hs_code_proposed.
    - Explicit input_version=1 and timestamps.
    """
    if not FIXTURES_FILE.exists():
        raise FileNotFoundError(f"Demo fixtures file not found: {FIXTURES_FILE}")

    with open(FIXTURES_FILE, encoding="utf-8") as f:
        data = json.load(f)

    shipments = data.get("shipments", [])
    print(f"Loaded {len(shipments)} demo shipments for company {company_id} from {FIXTURES_FILE}")

    with conn.cursor() as cur:
        cur.execute("SELECT id, name FROM companies WHERE id = %s;", (company_id,))
        comp = cur.fetchone()
        if not comp:
            raise ValueError(f"Company ID {company_id} not found in database.")
        print(f"Target company: {comp[1]} (ID: {comp[0]})")

        created_shipments = 0
        skipped_shipments = 0
        created_items = 0

        for s in shipments:
            s_num = s["shipment_number"]
            inv_num = s["invoice_number"]
            supp_name = s["supplier_name"]
            supp_email = s["supplier_email"]
            status = s["status"]
            curr = s["currency"]
            rate = Decimal(str(s["exchange_rate_demo"]))
            inv_tot = Decimal(str(s["invoice_total"]))
            cif_total_idr = inv_tot * rate
            readiness = "ready" if status in ("ready", "submitted", "arrived") else "incomplete"

            # Check if this shipment scenario already exists for this company
            cur.execute("""
                SELECT id, status, readiness_status
                FROM shipments
                WHERE company_id = %s AND shipment_number = %s;
            """, (company_id, s_num))
            existing_shipment = cur.fetchone()

            if existing_shipment:
                # Additive safety: preserve existing scenario, lifecycle, and reviewer edits entirely!
                skipped_shipments += 1
                continue

            # Insert missing shipment
            submitted_at = None
            arrived_at = None
            if status in ("submitted", "arrived"):
                submitted_at = "NOW()"
            if status == "arrived":
                arrived_at = "NOW()"

            cur.execute("""
                INSERT INTO shipments (
                    company_id, shipment_number, invoice_number, supplier_name, supplier_email,
                    status, readiness_status, currency, exchange_rate, cif_total_idr, total_duty_idr,
                    input_version, needs_action_rule_change, submitted_at, arrived_at, created_at, updated_at
                )
                VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, 0.0,
                    1, false,
                    CASE WHEN %s THEN NOW() ELSE NULL END,
                    CASE WHEN %s THEN NOW() ELSE NULL END,
                    NOW(), NOW()
                )
                RETURNING id;
            """, (
                company_id, s_num, inv_num, supp_name, supp_email,
                status, readiness, curr, rate, cif_total_idr,
                submitted_at is not None, arrived_at is not None,
            ))
            shipment_id = cur.fetchone()[0]
            created_shipments += 1

            # Insert items for new shipment
            for line_no, it in enumerate(s["items"], 1):
                qty = Decimal(str(it["quantity"]))
                uom_val = it.get("uom", "UNIT")
                price = Decimal(str(it["unit_price"]))
                line_total = Decimal(str(it["line_total"]))
                desc = it["description"]
                hs = it["hs_code"]

                # Ensure ready fixtures have items approved and accepted
                is_appr = status in ("ready", "submitted", "arrived")
                item_status = "approved" if is_appr else ("review" if status == "needs_review" else "draft")
                accepted_hs = hs if is_appr else None
                conf = Decimal("0.95") if is_appr else Decimal("0.85")
                risk = "low" if is_appr else "medium"

                cur.execute("""
                    INSERT INTO shipment_items (
                        shipment_id, company_id, line_no, description, quantity, uom,
                        unit_price, total_price_cif, hs_code_proposed, hs_code_accepted,
                        confidence_score, risk_level, status, is_approved, version,
                        created_at, updated_at
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s,
                        %s, %s, %s, %s, 1,
                        NOW(), NOW()
                    );
                """, (
                    shipment_id, company_id, line_no, desc, qty, uom_val,
                    price, line_total, hs, accepted_hs,
                    conf, risk, item_status, is_appr,
                ))
                created_items += 1

            # Sync documents for this shipment
            doc_specs = [
                ("INVOICE", f"{inv_num}.pdf", f"Commercial Invoice - {inv_num}", True),
                ("PACKING_LIST", f"{s.get('packing_list_number')}.pdf", f"Packing List - {s.get('packing_list_number')}", s.get("has_packing_list", True)),
                ("BL", f"{s.get('bl_number')}.pdf", f"Bill of Lading - {s.get('bl_number')}", s.get("has_bl", True)),
            ]
            if s.get("datasheet_code"):
                doc_specs.append(("DATASHEET", f"{s['datasheet_code']}.pdf", f"Technical Datasheet - {s['datasheet_code']}", True))

            for doc_type, f_name, parsed_title, is_provided in doc_specs:
                if not is_provided:
                    continue
                cur.execute("SELECT id FROM documents WHERE shipment_id = %s AND doc_type = %s;", (shipment_id, doc_type))
                if not cur.fetchone():
                    doc_disk_path = DOCS_DIR / f_name
                    f_size = doc_disk_path.stat().st_size if doc_disk_path.exists() else 3500
                    rel_path = f"data/demo/documents/{f_name}"
                    cur.execute("""
                        INSERT INTO documents (
                            shipment_id, company_id, doc_type, file_name, file_path, file_size, parsed_content, status, uploaded_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, 'provided', NOW());
                    """, (shipment_id, company_id, doc_type, f_name, rel_path, f_size, parsed_title))

            # Sync document checklist items
            checklist_defs = [
                ("INVOICE", "Commercial invoice", "DJBC", "provided"),
                ("PACKING_LIST", "Packing list", "DJBC", "provided" if s.get("has_packing_list", True) else "missing"),
                ("BL", "B/L atau AWB", "DJBC", "provided" if s.get("has_bl", True) else "missing"),
            ]
            for req_code, title, agency, check_status in checklist_defs:
                cur.execute("SELECT id FROM checklist_items WHERE shipment_id = %s AND requirement_code = %s;", (shipment_id, req_code))
                if not cur.fetchone():
                    cur.execute("""
                        INSERT INTO checklist_items (
                            shipment_id, item_id, company_id, requirement_code, title, agency, status, required_before_submission, verified_at
                        )
                        VALUES (%s, NULL, %s, %s, %s, %s, %s, true, CASE WHEN %s = 'provided' THEN NOW() ELSE NULL END);
                    """, (shipment_id, company_id, req_code, title, agency, check_status, check_status))

    print(
        f"Fixtures sync complete: {created_shipments} created, "
        f"{skipped_shipments} preserved existing shipments; {created_items} items created."
    )
    return len(shipments), created_items


def main():
    args = parse_args()
    conn, db_name = get_connection(args.db_url, args.live, args.apply)

    try:
        import_catalog(conn)
        import_fixtures(conn, args.company_id)
        conn.commit()
        print("Import completed successfully and committed.")
    except Exception as e:
        conn.rollback()
        print(f"Import failed with error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
