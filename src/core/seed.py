from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from src.core.database import SessionLocal, init_db
from src.core.security import get_password_hash
from src.models.entities import (
    Clarification,
    ClassificationMemory,
    Company,
    Document,
    DutyCalculation,
    HSCode,
    LartasRuleEntity,
    Shipment,
    ShipmentItem,
    User,
)


def seed_data(db: Session = None):
    init_db()
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        # 1. Company
        comp = db.query(Company).first()
        if not comp:
            comp = Company(
                name="PT Mitra Kemas Nusantara",
                npwp="01.234.567.8-012.000",
                is_active=True,
            )
            db.add(comp)
            db.flush()

        # 2. Users (3 Roles under PT Mitra Kemas Nusantara)
        users_data = [
            ("staf@mitrakemas.co.id", "Ahmad Staf Impor", "importer_staff"),
            ("reviewer@mitrakemas.co.id", "Budi Ahli Kepabeanan", "ppjk_reviewer"),
            ("admin@mitrakemas.co.id", "Siti Admin Logistik", "admin"),
        ]
        for email, name, role in users_data:
            u = db.query(User).filter_by(email=email).first()
            if not u:
                u = User(
                    company_id=1,
                    email=email,
                    full_name=name,
                    password_hash=get_password_hash("imporjaga123"),
                    role=role,
                    is_active=True,
                )
                db.add(u)

        # 3. Official HS Codes (Chapters 33, 61, 62, 84, 85 from data/seed/hs_codes.csv)
        import csv
        import os
        hs_csv = "/srv/hermes-control/services/agentic-import/data/seed/hs_codes.csv"
        if os.path.exists(hs_csv):
            with open(hs_csv, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    code_raw = r["code"].strip()
                    # Format as dotted e.g. 8481.80.99
                    code_dotted = f"{code_raw[:4]}.{code_raw[4:6]}.{code_raw[6:]}" if len(code_raw) == 8 else code_raw
                    for hs_variant in [code_raw, code_dotted]:
                        h = db.query(HSCode).filter_by(hs_code=hs_variant).first()
                        if not h:
                            h = HSCode(
                                hs_code=hs_variant,
                                description_id=f"Bab {r['chapter']} | Pos {r['heading']} | {r['description_raw']}",
                                description_en=r.get("description_en") or r["description_raw"],
                                bm_rate=float(r["bm_rate"]),
                                ppn_rate=11.0,
                                pph_rate=2.5,
                                lartas_coverage="verified_rules" if r["chapter"] in ("33", "84", "85", "61", "62") else "verified_none",
                                source="BTKI 2022 Official PMK 26/PMK.010/2022",
                            )
                            db.add(h)

        # 4. Lartas Rules (Official INSW)
        lartas_list = [
            ("8422", "LARTAS_LS_MESIN", "Laporan Surveyor Mesin & Peralatan", "Kemenperin", "LS_INDUSTRY", None),
            ("8501", "LARTAS_K3L_MOTOR", "Pendaftaran K3L / Standar Keselamatan Motor", "Kemendag", "K3L_SAFETY", None),
            ("8481", "LARTAS_PI_BAJA", "Persetujuan Impor Besi Baja & Produk Turunan", "Kemendag", "PI_STEEL", None),
            ("848180", "LARTAS_LS_VALVE", "Laporan Surveyor Katup & Valve Khusus", "Kemendag", "LS_VALVE_GROUP", None),
            ("3304", "LARTAS_BPOM_SKI", "Surat Keterangan Impor (SKI) Kosmetik", "BPOM", "BPOM_BORDER", None),
            ("6109", "LARTAS_PI_TPT", "Persetujuan Impor Tekstil & Produk Tekstil", "Kemendag", "PI_TEXTILE", None),
        ]
        for prefix, req_key, name, agency, group, super_id in lartas_list:
            lr = db.query(LartasRuleEntity).filter_by(hs_prefix=prefix, requirement_key=req_key).first()
            if not lr:
                lr = LartasRuleEntity(
                    company_id=None,  # Official rule
                    hs_prefix=prefix,
                    requirement_key=req_key,
                    permit_name=name,
                    issuing_agency=agency,
                    rule_group=group,
                    supersedes_rule_id=super_id,
                    is_active=True,
                    source="INSW Official Regulatory Database",
                )
                db.add(lr)

        # 5. Seed Historical Classification Memory (Human Decisions)
        mem_data = [
            ("Mesin Sealing Karton Otomatis 220V", "8422.30.00", {"fungsi": "sealing", "material": "stainless steel"}, "Klasifikasi disetujui Budi (Reviewer) sesuai BTKI 8422"),
            ("Motor Induksi AC 3-Fasa 1.5 kW 380V", "8501.52.19", {"daya": "1500W", "fasa": "3-phase"}, "Disetujui manusia untuk motor induksi industri standar"),
            ("PLC Control Panel Box Siemens S7-1200", "8537.10.19", {"voltase": "24V DC", "fungsi": "kontrol otomatis"}, "Papan kontrol programmable logic controller <= 1000V"),
        ]
        for desc, hs, attrs, notes in mem_data:
            m = db.query(ClassificationMemory).filter_by(company_id=1, hs_code=hs).first()
            if not m:
                m = ClassificationMemory(
                    company_id=1,
                    item_description=desc,
                    hs_code=hs,
                    matched_attributes=attrs,
                    decision_source="human_review",
                    human_decision_notes=f"[Seed Memory] {notes}",
                    is_active=True,
                )
                db.add(m)

        # 6. Skenario Demo Utama: MKN-011 (5 Barang Bab 84/85)
        now = datetime.now(UTC)
        mkn_011 = db.query(Shipment).filter_by(shipment_number="MKN-011").first()
        if not mkn_011:
            mkn_011 = Shipment(
                id=11,
                company_id=1,
                shipment_number="MKN-011",
                supplier_name="Shenzhen Packaging & Automation Co., Ltd.",
                supplier_email="tim-impor@mitrakemas.co.id",
                bl_number="OOCL-SZ-2026-9921",
                invoice_number="INV-2026-1104-01",
                currency="USD",
                exchange_rate=Decimal("16000.00"),
                cif_total_idr=Decimal("78940712.50"),
                total_duty_idr=Decimal("15139000.00"),
                readiness_status="incomplete",
                status="needs_clarification",
                input_version=1,
            )
            db.add(mkn_011)
            db.flush()

            # 5 Items for MKN-011
            items_mkn11 = [
                (1, "Mesin Sealing Karton Otomatis Model SK-500", 1, 1500.0, "8422.30.00", 0.94, "low", "approved", True),
                (2, "Motor Induksi AC 3-Phase 1.5 kW 380V IE3", 2, 350.0, "8501.52.19", 0.92, "low", "approved", True),
                (3, "Control Panel Box PLC Siemens S7-1200", 1, 800.0, "8537.10.19", 0.90, "low", "approved", True),
                (4, "Pneumatic Control Valve Actuator (Katup Ambigu)", 4, 180.0, "8481.80.90", 0.65, "medium", "needs_clarification", False),
                (5, "Inductive Proximity Sensor Switch NPN NO M12", 20, 15.0, "8543.70.90", 0.88, "low", "classified", False),
            ]
            for l_no, desc, qty, price, hs, conf, risk, st, approved in items_mkn11:
                it = ShipmentItem(
                    shipment_id=11,
                    company_id=1,
                    line_no=l_no,
                    description=desc,
                    quantity=Decimal(str(qty)),
                    unit_price=Decimal(str(price)),
                    total_price_cif=Decimal(str(qty * price * 16000)),
                    hs_code_proposed=hs,
                    hs_code_accepted=hs if approved else None,
                    confidence_score=Decimal(str(conf)),
                    risk_level=risk,
                    status=st,
                    is_approved=approved,
                    version=1,
                )
                db.add(it)
                db.flush()

                # Add duty calculation row for item 1
                if l_no == 1:
                    db.add(DutyCalculation(
                        shipment_id=11,
                        item_id=it.id,
                        company_id=1,
                        cif_idr=Decimal("78940712.50"),
                        bm_percentage=Decimal("5.0"),
                        bm_idr=Decimal("3948000.00"),
                        ppn_percentage=Decimal("11.0"),
                        ppn_idr=Decimal("9118000.00"),
                        pph_percentage=Decimal("2.5"),
                        pph_idr=Decimal("2073000.00"),
                        total_duties_idr=Decimal("15139000.00"),
                        is_current=True,
                    ))

                # Clarification question for Item 4 (Katup Ambigu)
                if l_no == 4:
                    db.add(Clarification(
                        shipment_id=11,
                        item_id=it.id,
                        company_id=1,
                        question="Apakah katup pneumatic ini dilengkapi actuator solenoid terintegrasi dan bertekanan kerja di atas 10 bar?",
                        attribute="tekanan_kerja_dan_actuator",
                        reason="Diperlukan untuk membedakan pos 8481.80.90 (katup industri) vs 8481.20 (katup transmisi fluida hidrolik/pneumatik).",
                        status="open",
                    ))

            # Initial Documents for MKN-011
            db.add(Document(
                shipment_id=11,
                company_id=1,
                doc_type="INVOICE",
                file_name="Invoice_MKN011_Shenzhen.pdf",
                file_path="/srv/hermes-control/services/agentic-import/data/vault/Invoice_MKN011_Shenzhen.pdf",
                file_size=425120,
                status="provided",
            ))
            db.add(Document(
                shipment_id=11,
                company_id=1,
                doc_type="PACKING_LIST",
                file_name="PackingList_MKN011.pdf",
                file_path="/srv/hermes-control/services/agentic-import/data/vault/PackingList_MKN011.pdf",
                file_size=212400,
                status="provided",
            ))
            db.add(Document(
                shipment_id=11,
                company_id=1,
                doc_type="BL",
                file_name="BillOfLading_OOCL_9921.pdf",
                file_path="/srv/hermes-control/services/agentic-import/data/vault/BillOfLading_OOCL_9921.pdf",
                file_size=315600,
                status="provided",
            ))
            db.add(Document(
                shipment_id=11,
                company_id=1,
                doc_type="DATASHEET",
                file_name="Datasheet_Pneumatic_Valve_Sample.pdf",
                file_path="/srv/hermes-control/services/agentic-import/data/vault/Datasheet_Pneumatic_Valve_Sample.pdf",
                file_size=154000,
                status="missing",  # Sengaja missing agar juri dapat mengunggah datasheet contoh
            ))

        # 7. Skenario MKN-007 (Ready H+5, Pos 8481)
        mkn_007 = db.query(Shipment).filter_by(shipment_number="MKN-007").first()
        if not mkn_007:
            mkn_007 = Shipment(
                id=7,
                company_id=1,
                shipment_number="MKN-007",
                supplier_name="Global Valve Technologies Inc.",
                supplier_email="tim-impor@mitrakemas.co.id",
                bl_number="MEDU-2026-7788",
                invoice_number="INV-GVT-007",
                currency="USD",
                exchange_rate=Decimal("16000.00"),
                cif_total_idr=Decimal("45000000.00"),
                total_duty_idr=Decimal("8600000.00"),
                readiness_status="ready",
                status="ready",
                input_version=1,
            )
            db.add(mkn_007)
            db.flush()
            db.add(ShipmentItem(
                shipment_id=7,
                company_id=1,
                line_no=1,
                description="Industrial Gate Valves 8481",
                quantity=Decimal(10),
                unit_price=Decimal("250.0"),
                total_price_cif=Decimal("40000000.00"),
                hs_code_proposed="8481.80.90",
                hs_code_accepted="8481.80.90",
                confidence_score=Decimal("0.95"),
                risk_level="low",
                status="approved",
                is_approved=True,
            ))

        # 8. Skenario MKN-008 (Submitted H+14, Pos 8481)
        mkn_008 = db.query(Shipment).filter_by(shipment_number="MKN-008").first()
        if not mkn_008:
            mkn_008 = Shipment(
                id=8,
                company_id=1,
                shipment_number="MKN-008",
                supplier_name="Hydraulic & Pneumatic Systems Ltd.",
                supplier_email="tim-impor@mitrakemas.co.id",
                bl_number="MAEU-2026-8899",
                invoice_number="INV-HPS-008",
                currency="USD",
                exchange_rate=Decimal("16000.00"),
                cif_total_idr=Decimal("62000000.00"),
                total_duty_idr=Decimal("11800000.00"),
                readiness_status="ready",
                status="submitted",
                submitted_at=now - timedelta(days=2),
                input_version=1,
            )
            db.add(mkn_008)
            db.flush()
            db.add(ShipmentItem(
                shipment_id=8,
                company_id=1,
                line_no=1,
                description="High Pressure Regulating Valves 8481",
                quantity=Decimal(15),
                unit_price=Decimal("200.0"),
                total_price_cif=Decimal("48000000.00"),
                hs_code_proposed="8481.10.99",
                hs_code_accepted="8481.10.99",
                confidence_score=Decimal("0.96"),
                risk_level="low",
                status="approved",
                is_approved=True,
            ))

        # 9. Skenario MKN-003 (Arrived, Pos 8481)
        mkn_003 = db.query(Shipment).filter_by(shipment_number="MKN-003").first()
        if not mkn_003:
            mkn_003 = Shipment(
                id=3,
                company_id=1,
                shipment_number="MKN-003",
                supplier_name="Tokyo Valve Corporation",
                supplier_email="tim-impor@mitrakemas.co.id",
                bl_number="ONE-2026-3344",
                invoice_number="INV-TVC-003",
                currency="USD",
                exchange_rate=Decimal("16000.00"),
                cif_total_idr=Decimal("35000000.00"),
                total_duty_idr=Decimal("6700000.00"),
                readiness_status="ready",
                status="arrived",
                submitted_at=now - timedelta(days=10),
                arrived_at=now - timedelta(days=1),
                input_version=1,
            )
            db.add(mkn_003)
            db.flush()
            db.add(ShipmentItem(
                shipment_id=3,
                company_id=1,
                line_no=1,
                description="Brass Ball Valves 8481",
                quantity=Decimal(50),
                unit_price=Decimal("40.0"),
                total_price_cif=Decimal("32000000.00"),
                hs_code_proposed="8481.80.11",
                hs_code_accepted="8481.80.11",
                confidence_score=Decimal("0.98"),
                risk_level="low",
                status="approved",
                is_approved=True,
            ))

        db.commit()
        print("Database initialized and seeded successfully for PT Mitra Kemas Nusantara (MKN-011, MKN-007, MKN-008, MKN-003)!")
    finally:
        if close_db:
            db.close()


if __name__ == "__main__":
    seed_data()
