import csv
import os
import uuid
import psycopg
from src.core.security import get_password_hash

DB_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://imporjaga_user:imporjaga@127.0.0.1:5432/imporjaga"
)

if not os.environ.get("DATABASE_URL"):
    env_file = "/srv/hermes-control/services/agentic-import/.env"
    if os.path.exists(env_file):
        with open(env_file) as f:
            for line in f:
                if line.startswith("DATABASE_URL="):
                    DB_URL = line.split("=", 1)[1].strip()


def ingest():
    print(f"Connecting to database: {DB_URL}")
    with psycopg.connect(DB_URL) as conn:
        with conn.cursor() as cur:
            # 1. Company
            cur.execute("SELECT id FROM companies LIMIT 1;")
            row = cur.fetchone()
            if not row:
                cid = str(uuid.uuid4())
                cur.execute("""
                    INSERT INTO companies (id, name, tax_id, npwp, has_api, autonomy_level, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW()) RETURNING id;
                """, (cid, "PT Mitra Kemas Nusantara", "01.234.567.8-012.000", "01.234.567.8-012.000", True, "auto"))
                company_id = cid
            else:
                company_id = row[0]
            print(f"Company PT Mitra Kemas Nusantara ready: {company_id}")

            # 2. Users (3 Roles under PT Mitra Kemas Nusantara)
            pw_hash = get_password_hash("imporjaga123")
            users_data = [
                ("staf@mitrakemas.co.id", "Ahmad Staf Impor", "importer_staff"),
                ("reviewer@mitrakemas.co.id", "Budi Ahli Kepabeanan", "ppjk_reviewer"),
                ("admin@mitrakemas.co.id", "Siti Admin Logistik", "admin"),
            ]
            for email, name, role in users_data:
                cur.execute("SELECT id FROM users WHERE email = %s;", (email,))
                if not cur.fetchone():
                    cur.execute("""
                        INSERT INTO users (id, company_id, email, password_hash, full_name, role, is_active, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW());
                    """, (str(uuid.uuid4()), company_id, email, pw_hash, name, role, True))
            print("Users seeded (staf, reviewer, admin).")

            # 3. Regulations
            reg_map = {}
            reg_path = "data/seed/regulations.csv"
            if os.path.exists(reg_path):
                with open(reg_path, mode="r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for r in reader:
                        cur.execute("SELECT id FROM regulations WHERE number = %s;", (r["number"],))
                        res = cur.fetchone()
                        if not res:
                            cur.execute("""
                                INSERT INTO regulations (number, title, issuer, summary, effective_date, source_url, is_simulated, created_at)
                                VALUES (%s, %s, %s, %s, %s, %s, false, NOW()) RETURNING id;
                            """, (r["number"], r["title"], r["issuer"], r["summary"], r["effective_date"], r["source_url"]))
                            reg_id = cur.fetchone()[0]
                        else:
                            reg_id = res[0]
                        reg_map[r["number"]] = reg_id
            print(f"Regulations ingested: {len(reg_map)}")

            # 4. Exchange Rates
            ex_path = "data/seed/exchange_rates.csv"
            if os.path.exists(ex_path):
                with open(ex_path, mode="r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for r in reader:
                        cur.execute("SELECT id FROM exchange_rates WHERE currency = %s AND valid_from = %s;", (r["currency"], r["valid_from"]))
                        if not cur.fetchone():
                            cur.execute("""
                                INSERT INTO exchange_rates (currency, rate_idr, valid_from, valid_to, source)
                                VALUES (%s, %s, %s, %s, %s);
                            """, (r["currency"], r["rate_idr"], r["valid_from"], r["valid_to"], r["source"]))
            print("Exchange rates ingested.")

            # 5. HS Codes
            hs_count = 0
            hs_path = "data/seed/hs_codes.csv"
            if os.path.exists(hs_path):
                with open(hs_path, mode="r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for r in reader:
                        cur.execute("SELECT id FROM hs_codes WHERE code = %s;", (r["code"],))
                        if not cur.fetchone():
                            cur.execute("""
                                INSERT INTO hs_codes (code, chapter, heading, subheading, description_raw, description_id, description_en, unit, bm_rate, is_luxury, lartas_coverage, note, created_at)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW());
                            """, (
                                r["code"], r["chapter"], r["heading"], r["subheading"],
                                r["description_raw"], r["description_raw"], r.get("description_en", ""),
                                r.get("unit", "u"), float(r["bm_rate"]), r.get("is_luxury", "false").lower() == "true",
                                "verified_rules" if r["chapter"] in ("33", "84", "85") else "verified_none",
                                r.get("note", "")
                            ))
                            hs_count += 1
            print(f"HS Codes ingested: {hs_count}")

            # 6. Lartas Rules
            lartas_count = 0
            lartas_path = "data/seed/lartas_rules.csv"
            if os.path.exists(lartas_path):
                with open(lartas_path, mode="r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for r in reader:
                        reg_id = reg_map.get(r["regulation_number"], 1)
                        cur.execute("SELECT id FROM lartas_rules WHERE hs_prefix = %s AND requirement_key = %s;", (r["hs_prefix"], r.get("requirement_key", "")))
                        if not cur.fetchone():
                            cur.execute("""
                                INSERT INTO lartas_rules (hs_prefix, regulation_id, permit_name, permit_code, issuing_agency, stage, requires_surveyor, effective_from, requirement_key, rule_group, source_url, note)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                            """, (
                                r["hs_prefix"], reg_id, r["permit_name"], r.get("permit_code", ""),
                                r["issuing_agency"], r.get("stage", "border"), r.get("requires_surveyor", "false").lower() == "true",
                                r["effective_from"], r.get("requirement_key", r["permit_name"]),
                                r.get("rule_group", "GENERAL"), r.get("source_url", ""), r.get("note", "")
                            ))
                            lartas_count += 1
            print(f"Lartas rules ingested: {lartas_count}")

            # 7. PPh 22 Rates
            pph_count = 0
            pph_path = "data/seed/pph22_lampiran.csv"
            if os.path.exists(pph_path):
                with open(pph_path, mode="r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for r in reader:
                        cur.execute("SELECT id FROM pph22_rates WHERE hs_code = %s;", (r["hs_code"],))
                        if not cur.fetchone():
                            cur.execute("""
                                INSERT INTO pph22_rates (hs_code, lampiran, rate, regulation)
                                VALUES (%s, %s, %s, %s);
                            """, (r["hs_code"], r["lampiran"], float(r["rate"]), r["regulation"]))
                            pph_count += 1
            print(f"PPh 22 rates ingested: {pph_count}")

            # 8. Skenario Demo MKN-011 (5 Barang Bab 84/85)
            cur.execute("DELETE FROM shipments WHERE reference_no IN ('MKN-011', 'MKN-IMP-2611-011');")
            s11_id = str(uuid.uuid4())
            cur.execute("""
                INSERT INTO shipments (id, company_id, reference_no, invoice_no, supplier_name, supplier_email,
                                       incoterm, transport_mode, origin_country, currency, total_invoice_amount,
                                       freight_amount, insurance_amount, status, readiness_status, input_version,
                                       created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()) RETURNING id;
            """, (
                s11_id, company_id, "MKN-011", "INV-MKN-011",
                "Shenzhen Packaging & Automation Co., Ltd.", "tim-impor@mitrakemas.co.id",
                "CIF", "sea", "CN", "USD", 4933.79, 0.0, 0.0,
                "needs_clarification", "incomplete", 1
            ))

            # 5 Barang Bab 84/85
            items = [
                (1, "Mesin Sealing Karton Otomatis Model SK-500", 1, 1500.0, "84223000", 0.94, "low", "approved"),
                (2, "Motor Induksi AC 3-Phase 1.5 kW 380V IE3", 2, 350.0, "85015219", 0.92, "low", "approved"),
                (3, "Control Panel Box PLC Siemens S7-1200", 1, 800.0, "85371019", 0.90, "low", "approved"),
                (4, "Pneumatic Control Valve Actuator (Katup Ambigu)", 4, 180.0, "84818090", 0.65, "medium", "needs_clarification"),
                (5, "Inductive Proximity Sensor Switch NPN NO M12", 20, 15.0, "85437090", 0.88, "low", "classified"),
            ]
            for l_no, desc, qty, price, hs, conf, risk, st in items:
                it_id = str(uuid.uuid4())
                cur.execute("""
                    INSERT INTO shipment_items (id, shipment_id, company_id, line_no, description_raw,
                                               qty, unit, unit_price, total_price,
                                               status, input_version, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()) RETURNING id;
                """, (it_id, s11_id, company_id, l_no, desc, qty, "UNIT", price, qty * price, st, 1))

                # HS Classification row
                cur.execute("""
                    INSERT INTO hs_classifications (id, item_id, company_id, hs_code, confidence_score,
                                                    llm_confidence, retrieval_score, justification, alternatives_json,
                                                    status, decided_by, is_current, input_version, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW());
                """, (str(uuid.uuid4()), it_id, company_id, hs, conf, conf, 0.90, f"Analisis teknis spesifikasi barang pos {hs[:4]}", "[]", "approved" if st == "approved" else "proposed", "agent", True, 1))

                # Clarification question for Item 4 (Katup Ambigu)
                if l_no == 4:
                    cur.execute("""
                        INSERT INTO clarifications (id, shipment_id, item_id, company_id, question_text,
                                                    status, channel, created_at, attribute, reason)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), %s, %s);
                    """, (
                        str(uuid.uuid4()), s11_id, it_id, company_id,
                        "Apakah katup pneumatic ini dilengkapi actuator solenoid terintegrasi dan bertekanan kerja di atas 10 bar?",
                        "open", "supplier", "tekanan_kerja_dan_actuator",
                        "Diperlukan untuk membedakan pos 8481.80.90 (katup industri) vs 8481.20 (katup transmisi fluida hidrolik/pneumatik)."
                    ))
            print("MKN-011 shipment and 5 items seeded.")

            # 9. MKN-007 (Ready, H+5, Pos 8481)
            cur.execute("SELECT id FROM shipments WHERE reference_no = 'MKN-007';")
            if not cur.fetchone():
                cur.execute("""
                    INSERT INTO shipments (id, company_id, reference_no, invoice_no, supplier_name, supplier_email,
                                           incoterm, transport_mode, origin_country, currency, total_invoice_amount,
                                           freight_amount, insurance_amount, status, readiness_status, input_version,
                                           created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW());
                """, (
                    str(uuid.uuid4()), company_id, "MKN-007", "INV-GVT-007",
                    "Global Valve Technologies Inc.", "tim-impor@mitrakemas.co.id",
                    "CIF", "sea", "US", "USD", 2812.50, 0.0, 0.0,
                    "ready", "ready", 1
                ))

            # 10. MKN-008 (Submitted, H+14, Pos 8481)
            cur.execute("SELECT id FROM shipments WHERE reference_no = 'MKN-008';")
            if not cur.fetchone():
                cur.execute("""
                    INSERT INTO shipments (id, company_id, reference_no, invoice_no, supplier_name, supplier_email,
                                           incoterm, transport_mode, origin_country, currency, total_invoice_amount,
                                           freight_amount, insurance_amount, status, readiness_status, input_version,
                                           submitted_at, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW() - INTERVAL '2 days', NOW(), NOW());
                """, (
                    str(uuid.uuid4()), company_id, "MKN-008", "INV-HPS-008",
                    "Hydraulic & Pneumatic Systems Ltd.", "tim-impor@mitrakemas.co.id",
                    "CIF", "sea", "DE", "USD", 3875.00, 0.0, 0.0,
                    "submitted", "ready", 1
                ))

            # 11. MKN-003 (Arrived, Pos 8481)
            cur.execute("SELECT id FROM shipments WHERE reference_no = 'MKN-003';")
            if not cur.fetchone():
                cur.execute("""
                    INSERT INTO shipments (id, company_id, reference_no, invoice_no, supplier_name, supplier_email,
                                           incoterm, transport_mode, origin_country, currency, total_invoice_amount,
                                           freight_amount, insurance_amount, status, readiness_status, input_version,
                                           submitted_at, arrived_at, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW() - INTERVAL '10 days', NOW() - INTERVAL '1 day', NOW(), NOW());
                """, (
                    str(uuid.uuid4()), company_id, "MKN-003", "INV-TVC-003",
                    "Tokyo Valve Corporation", "tim-impor@mitrakemas.co.id",
                    "CIF", "sea", "JP", "USD", 2187.50, 0.0, 0.0,
                    "arrived", "ready", 1
                ))

        conn.commit()
    print("Database seeding completed successfully!")


if __name__ == "__main__":
    ingest()
