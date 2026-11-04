import json
import shutil
import subprocess
from decimal import Decimal
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parents[1]
DATA_DEMO = ROOT / "data" / "demo"
DOCS_DIR = DATA_DEMO / "documents"


def build_shipments_dataset():
    shipments_data = [
        {
            "shipment_number": "MKN-DEMO-001",
            "invoice_number": "INV-DEMO-MKN-001",
            "packing_list_number": "PKL-DEMO-MKN-001",
            "bl_number": "BL-DEMO-MKN-001",
            "status": "ready",
            "supplier_name": "Apex Automation Machinery Co., Ltd.",
            "supplier_email": "export@apex-automation.example",
            "origin_country": "CN",
            "currency": "USD",
            "exchange_rate_demo": "16200.00",
            "approval_notes": "DEMO fixture: synthetic pre-approved record for demonstration only",
            "has_packing_list": True,
            "has_bl": True,
            "datasheet_code": "DS-APX-M8422",
            "items": [
                {
                    "sku": "APX-M8422-FL",
                    "uom": "SET",
                    "description": "[APX-M8422-FL] Automatic Liquid Bottle Filling Machine 2.2kW 380V 50Hz with Multi-Head Stainless Steel Dispenser",
                    "hs_code": "84223000",
                    "quantity": "2",
                    "unit_price": "4500.00",
                    "line_total": "9000.00",
                    "packages": "2 Crates",
                    "net_weight_kg": "1450.0",
                    "gross_weight_kg": "1620.0",
                },
                {
                    "sku": "APX-M8422-WR",
                    "uom": "SET",
                    "description": "[APX-M8422-WR] Heat-Shrink Film Packaging and Wrapping Machine with Digital PID Temperature Controller",
                    "hs_code": "84224000",
                    "quantity": "1",
                    "unit_price": "6200.00",
                    "line_total": "6200.00",
                    "packages": "1 Crate",
                    "net_weight_kg": "850.0",
                    "gross_weight_kg": "980.0",
                },
            ],
            "invoice_total": "15200.00",
        },
        {
            "shipment_number": "MKN-DEMO-002",
            "invoice_number": "INV-DEMO-MKN-002",
            "packing_list_number": "PKL-DEMO-MKN-002",
            "bl_number": "BL-DEMO-MKN-002",
            "status": "needs_review",
            "supplier_name": "Nordic Flow Controls AB",
            "supplier_email": "sales@nordic-flow.example",
            "origin_country": "SE",
            "currency": "USD",
            "exchange_rate_demo": "16200.00",
            "approval_notes": "DEMO fixture: awaiting classification review for high-pressure valve",
            "has_packing_list": True,
            "has_bl": True,
            "datasheet_code": "DS-NFC-V8481",
            "items": [
                {
                    "sku": "NFC-V8481-PN",
                    "uom": "PCS",
                    "description": "[NFC-V8481-PN] Pneumatic Control Actuator Valve PN16 DN50 Flanged with Smart Positioner",
                    "hs_code": "84818099",
                    "quantity": "8",
                    "unit_price": "340.00",
                    "line_total": "2720.00",
                    "packages": "2 Boxes",
                    "net_weight_kg": "96.0",
                    "gross_weight_kg": "110.0",
                },
                {
                    "sku": "NFC-V8481-PR",
                    "uom": "PCS",
                    "description": "[NFC-V8481-PR] Direct Acting Pressure Reducing Regulator Valve 1-inch Female Threaded",
                    "hs_code": "84811099",
                    "quantity": "12",
                    "unit_price": "185.00",
                    "line_total": "2220.00",
                    "packages": "3 Boxes",
                    "net_weight_kg": "72.0",
                    "gross_weight_kg": "85.0",
                },
            ],
            "invoice_total": "4940.00",
        },
        {
            "shipment_number": "MKN-DEMO-003",
            "invoice_number": "INV-DEMO-MKN-003",
            "packing_list_number": "PKL-DEMO-MKN-003",
            "bl_number": "BL-DEMO-MKN-003",
            "status": "needs_clarification",
            "supplier_name": "Dongguan Precision Motors Ltd.",
            "supplier_email": "support@dg-motors.example",
            "origin_country": "CN",
            "currency": "USD",
            "exchange_rate_demo": "16200.00",
            "approval_notes": "DEMO fixture: needs supplier clarification on motor output power kW",
            "has_packing_list": True,
            "has_bl": True,
            "datasheet_code": "DS-DGM-MOT",
            "items": [
                {
                    "sku": "DGM-MOT-3PH",
                    "uom": "UNIT",
                    "description": "[DGM-MOT-3PH] Three-Phase AC Asynchronous Induction Motor 1.5kW 1400rpm IP55 Class F Insulation",
                    "hs_code": "85015219",
                    "quantity": "15",
                    "unit_price": "210.00",
                    "line_total": "3150.00",
                    "packages": "5 Crates",
                    "net_weight_kg": "375.0",
                    "gross_weight_kg": "420.0",
                },
                {
                    "sku": "DGM-SW-LIMIT",
                    "uom": "PCS",
                    "description": "[DGM-SW-LIMIT] Heavy Duty Industrial Roller Lever Limit Switch 250V 10A Waterproof Sealed Enclosure",
                    "hs_code": "85365099",
                    "quantity": "50",
                    "unit_price": "18.50",
                    "line_total": "925.00",
                    "packages": "2 Cartons",
                    "net_weight_kg": "25.0",
                    "gross_weight_kg": "30.0",
                },
            ],
            "invoice_total": "4075.00",
        },
        {
            "shipment_number": "MKN-DEMO-004",
            "invoice_number": "INV-DEMO-MKN-004",
            "packing_list_number": "PKL-DEMO-MKN-004",
            "bl_number": "BL-DEMO-MKN-004",
            "status": "draft",
            "supplier_name": "Zhejiang Safety Apparel Corp.",
            "supplier_email": "orders@zj-apparel.example",
            "origin_country": "CN",
            "currency": "USD",
            "exchange_rate_demo": "16200.00",
            "approval_notes": "DEMO fixture: draft shipment in initial data entry",
            "has_packing_list": False,
            "has_bl": False,
            "datasheet_code": None,
            "items": [
                {
                    "sku": "ZJA-PNT-CTN",
                    "uom": "PCS",
                    "description": "[ZJA-PNT-CTN] Men Industrial Protective Work Pants Heavy Cotton Twill with Reinforced Knee Pads",
                    "hs_code": "62034290",
                    "quantity": "200",
                    "unit_price": "14.50",
                    "line_total": "2900.00",
                    "packages": "10 Cartons",
                    "net_weight_kg": "140.0",
                    "gross_weight_kg": "155.0",
                },
                {
                    "sku": "ZJA-TSH-CTN",
                    "uom": "PCS",
                    "description": "[ZJA-TSH-CTN] Crewneck Cotton Workwear Uniform T-Shirt Short Sleeve 200gsm Breathable",
                    "hs_code": "61091010",
                    "quantity": "400",
                    "unit_price": "5.50",
                    "line_total": "2200.00",
                    "packages": "8 Cartons",
                    "net_weight_kg": "95.0",
                    "gross_weight_kg": "108.0",
                },
            ],
            "invoice_total": "5100.00",
        },
        {
            "shipment_number": "MKN-DEMO-005",
            "invoice_number": "INV-DEMO-MKN-005",
            "packing_list_number": "PKL-DEMO-MKN-005",
            "bl_number": "BL-DEMO-MKN-005",
            "status": "needs_documents",
            "supplier_name": "BioBotanica Ingredients Inc.",
            "supplier_email": "customs@biobotanica.example",
            "origin_country": "FR",
            "currency": "USD",
            "exchange_rate_demo": "16200.00",
            "approval_notes": "DEMO fixture: waiting for Certificate of Analysis & Phytosanitary",
            "has_packing_list": True,
            "has_bl": False,
            "datasheet_code": "DS-BBI-OIL",
            "items": [
                {
                    "sku": "BBI-OIL-SAN",
                    "uom": "KG",
                    "description": "[BBI-OIL-SAN] Pure Sandalwood Essential Oil Aroma Grade Food Contact Aluminum Canister 1kg",
                    "hs_code": "33012920",
                    "quantity": "10",
                    "unit_price": "850.00",
                    "line_total": "8500.00",
                    "packages": "1 Carton",
                    "net_weight_kg": "10.0",
                    "gross_weight_kg": "13.5",
                },
                {
                    "sku": "BBI-OIL-PAT",
                    "uom": "KG",
                    "description": "[BBI-OIL-PAT] Pure Fractionated Patchouli Essential Oil Industrial Fragrance Blend 5kg Drum",
                    "hs_code": "33012960",
                    "quantity": "25",
                    "unit_price": "140.00",
                    "line_total": "3500.00",
                    "packages": "5 Drums",
                    "net_weight_kg": "25.0",
                    "gross_weight_kg": "31.0",
                },
            ],
            "invoice_total": "12000.00",
        },
        {
            "shipment_number": "MKN-DEMO-006",
            "invoice_number": "INV-DEMO-MKN-006",
            "packing_list_number": "PKL-DEMO-MKN-006",
            "bl_number": "BL-DEMO-MKN-006",
            "status": "submitted",
            "supplier_name": "Ebara Hydro Technologies Ltd.",
            "supplier_email": "shipping@ebara-hydro.example",
            "origin_country": "JP",
            "currency": "USD",
            "exchange_rate_demo": "16200.00",
            "approval_notes": "DEMO fixture: customs declaration submitted to INSW portal",
            "has_packing_list": True,
            "has_bl": True,
            "datasheet_code": None,
            "items": [
                {
                    "sku": "EHT-PMP-CNT",
                    "uom": "UNIT",
                    "description": "[EHT-PMP-CNT] Stainless Steel Horizontal Centrifugal Water Pump 7.5kW 2900rpm Cast Iron Casing",
                    "hs_code": "84137099",
                    "quantity": "4",
                    "unit_price": "1750.00",
                    "line_total": "7000.00",
                    "packages": "4 Crates",
                    "net_weight_kg": "480.0",
                    "gross_weight_kg": "550.0",
                },
                {
                    "sku": "EHT-FLT-IND",
                    "uom": "SET",
                    "description": "[EHT-FLT-IND] Multi-Cartridge Industrial Water Purification Filter Unit with Differential Gauge",
                    "hs_code": "84212122",
                    "quantity": "2",
                    "unit_price": "3100.00",
                    "line_total": "6200.00",
                    "packages": "2 Crates",
                    "net_weight_kg": "320.0",
                    "gross_weight_kg": "380.0",
                },
            ],
            "invoice_total": "13200.00",
        },
        {
            "shipment_number": "MKN-DEMO-007",
            "invoice_number": "INV-DEMO-MKN-007",
            "packing_list_number": "PKL-DEMO-MKN-007",
            "bl_number": "BL-DEMO-MKN-007",
            "status": "arrived",
            "supplier_name": "Siemens Process Control AG",
            "supplier_email": "logistics@siemens-pc.example",
            "origin_country": "DE",
            "currency": "USD",
            "exchange_rate_demo": "16200.00",
            "approval_notes": "DEMO fixture: cargo arrived at Tanjung Priok Port, customs cleared",
            "has_packing_list": True,
            "has_bl": True,
            "datasheet_code": "DS-SPC-PLC",
            "items": [
                {
                    "sku": "SPC-PLC-S7",
                    "uom": "UNIT",
                    "description": "[SPC-PLC-S7] Programmable Logic Controller Automation Panel S7-1500 CPU 1515-2 PN Modular Unit",
                    "hs_code": "85371019",
                    "quantity": "2",
                    "unit_price": "5400.00",
                    "line_total": "10800.00",
                    "packages": "2 Cases",
                    "net_weight_kg": "38.0",
                    "gross_weight_kg": "46.0",
                },
                {
                    "sku": "SPC-VLV-BL",
                    "uom": "PCS",
                    "description": "[SPC-VLV-BL] Forged Brass Industrial Ball Valve Full Bore 2-inch with ISO 5211 Direct Mounting Pad",
                    "hs_code": "84818011",
                    "quantity": "20",
                    "unit_price": "65.00",
                    "line_total": "1300.00",
                    "packages": "2 Cartons",
                    "net_weight_kg": "44.0",
                    "gross_weight_kg": "50.0",
                },
            ],
            "invoice_total": "12100.00",
        },
        {
            "shipment_number": "MKN-DEMO-008",
            "invoice_number": "INV-DEMO-MKN-008",
            "packing_list_number": "PKL-DEMO-MKN-008",
            "bl_number": "BL-DEMO-MKN-008",
            "status": "draft",
            "supplier_name": "Hangzhou Conveyor Systems Co.",
            "supplier_email": "sales@hz-conveyor.example",
            "origin_country": "CN",
            "currency": "USD",
            "exchange_rate_demo": "16200.00",
            "approval_notes": "DEMO fixture: draft shipment under quotation review",
            "has_packing_list": False,
            "has_bl": False,
            "datasheet_code": None,
            "items": [
                {
                    "sku": "HZC-MC-WR84",
                    "uom": "SET",
                    "description": "[HZC-MC-WR84] Semi-Automatic Shrink Sleeve Wrapping Machine with In-Feed Roller Table 1.8kW",
                    "hs_code": "84224000",
                    "quantity": "2",
                    "unit_price": "3800.00",
                    "line_total": "7600.00",
                    "packages": "2 Crates",
                    "net_weight_kg": "750.0",
                    "gross_weight_kg": "860.0",
                },
                {
                    "sku": "HZC-SW-IND",
                    "uom": "PCS",
                    "description": "[HZC-SW-IND] Industrial Emergency Stop Push Button Switch 24V Mushroom Head with Key Release",
                    "hs_code": "85365099",
                    "quantity": "25",
                    "unit_price": "24.00",
                    "line_total": "600.00",
                    "packages": "1 Carton",
                    "net_weight_kg": "12.0",
                    "gross_weight_kg": "15.0",
                },
            ],
            "invoice_total": "8200.00",
        },
        {
            "shipment_number": "MKN-DEMO-009",
            "invoice_number": "INV-DEMO-MKN-009",
            "packing_list_number": "PKL-DEMO-MKN-009",
            "bl_number": "BL-DEMO-MKN-009",
            "status": "needs_clarification",
            "supplier_name": "Guangdong Valve Manufacturing Corp.",
            "supplier_email": "export@gd-valves.example",
            "origin_country": "CN",
            "currency": "USD",
            "exchange_rate_demo": "16200.00",
            "approval_notes": "DEMO fixture: question sent to supplier regarding valve seat material",
            "has_packing_list": True,
            "has_bl": True,
            "datasheet_code": None,
            "items": [
                {
                    "sku": "GDV-BV-BRASS",
                    "uom": "PCS",
                    "description": "[GDV-BV-BRASS] Brass Ball Valve Threaded Female NPT 3/4-inch PTFE Seats Nickel Plated Handle",
                    "hs_code": "84818011",
                    "quantity": "100",
                    "unit_price": "22.00",
                    "line_total": "2200.00",
                    "packages": "4 Cartons",
                    "net_weight_kg": "90.0",
                    "gross_weight_kg": "102.0",
                },
                {
                    "sku": "GDV-PR-REG",
                    "uom": "PCS",
                    "description": "[GDV-PR-REG] Pneumatic Pressure Regulator Valve with Pressure Gauge 0-10 Bar Filter Lubricator Unit",
                    "hs_code": "84811099",
                    "quantity": "30",
                    "unit_price": "75.00",
                    "line_total": "2250.00",
                    "packages": "2 Cartons",
                    "net_weight_kg": "45.0",
                    "gross_weight_kg": "52.0",
                },
            ],
            "invoice_total": "4450.00",
        },
        {
            "shipment_number": "MKN-DEMO-010",
            "invoice_number": "INV-DEMO-MKN-010",
            "packing_list_number": "PKL-DEMO-MKN-010",
            "bl_number": "BL-DEMO-MKN-010",
            "status": "needs_review",
            "supplier_name": "Kyoto Precision Electric Works",
            "supplier_email": "orders@kyoto-electric.example",
            "origin_country": "JP",
            "currency": "USD",
            "exchange_rate_demo": "16200.00",
            "approval_notes": "DEMO fixture: review needed for multi-function PLC equipment",
            "has_packing_list": True,
            "has_bl": True,
            "datasheet_code": None,
            "items": [
                {
                    "sku": "KPE-PLC-MOD",
                    "uom": "UNIT",
                    "description": "[KPE-PLC-MOD] Industrial Micro PLC Controller Panel 24V DC Digital I/O RS-485 Modbus RTU",
                    "hs_code": "85371019",
                    "quantity": "3",
                    "unit_price": "1800.00",
                    "line_total": "5400.00",
                    "packages": "3 Boxes",
                    "net_weight_kg": "42.0",
                    "gross_weight_kg": "50.0",
                },
                {
                    "sku": "KPE-MOT-ASYNC",
                    "uom": "UNIT",
                    "description": "[KPE-MOT-ASYNC] Explosion-Proof Asynchronous AC Electric Motor 3.7kW 380V Ex d IIB T4 Gb Certified",
                    "hs_code": "85015219",
                    "quantity": "4",
                    "unit_price": "650.00",
                    "line_total": "2600.00",
                    "packages": "4 Crates",
                    "net_weight_kg": "280.0",
                    "gross_weight_kg": "320.0",
                },
            ],
            "invoice_total": "8000.00",
        },
        {
            "shipment_number": "MKN-DEMO-011",
            "invoice_number": "INV-DEMO-MKN-011",
            "packing_list_number": "PKL-DEMO-MKN-011",
            "bl_number": "BL-DEMO-MKN-011",
            "status": "needs_documents",
            "supplier_name": "Shanghai Packing Solutions Ltd.",
            "supplier_email": "support@sh-packing.example",
            "origin_country": "CN",
            "currency": "USD",
            "exchange_rate_demo": "16200.00",
            "approval_notes": "DEMO fixture: bill of lading endorsed copy requested from carrier",
            "has_packing_list": True,
            "has_bl": False,
            "datasheet_code": None,
            "items": [
                {
                    "sku": "SHP-FILL-BOT",
                    "uom": "SET",
                    "description": "[SHP-FILL-BOT] Rotary Automatic Capping and Labeling Machine Unit 3.5kW 24 BPM Capacity",
                    "hs_code": "84223000",
                    "quantity": "1",
                    "unit_price": "7800.00",
                    "line_total": "7800.00",
                    "packages": "1 Crate",
                    "net_weight_kg": "920.0",
                    "gross_weight_kg": "1050.0",
                },
                {
                    "sku": "SHP-WRAP-PL",
                    "uom": "SET",
                    "description": "[SHP-WRAP-PL] Pallet Stretch Film Wrapping Machine Automatic Turntable 1500kg Load Cell System",
                    "hs_code": "84224000",
                    "quantity": "2",
                    "unit_price": "4100.00",
                    "line_total": "8200.00",
                    "packages": "2 Crates",
                    "net_weight_kg": "1100.0",
                    "gross_weight_kg": "1260.0",
                },
            ],
            "invoice_total": "16000.00",
        },
        {
            "shipment_number": "MKN-DEMO-012",
            "invoice_number": "INV-DEMO-MKN-012",
            "packing_list_number": "PKL-DEMO-MKN-012",
            "bl_number": "BL-DEMO-MKN-012",
            "status": "ready",
            "supplier_name": "Taizhou Sanitary Fittings Co.",
            "supplier_email": "sales@taizhou-fittings.example",
            "origin_country": "CN",
            "currency": "USD",
            "exchange_rate_demo": "16200.00",
            "approval_notes": "DEMO fixture: verification passed, ready for PIB generation",
            "has_packing_list": True,
            "has_bl": True,
            "datasheet_code": None,
            "items": [
                {
                    "sku": "TZF-VLV-BALL",
                    "uom": "PCS",
                    "description": "[TZF-VLV-BALL] Brass Forged Nickel-Plated Ball Valve 1-1/2 inch BSP Female Full Port 600 WOG",
                    "hs_code": "84818011",
                    "quantity": "80",
                    "unit_price": "35.00",
                    "line_total": "2800.00",
                    "packages": "4 Cartons",
                    "net_weight_kg": "88.0",
                    "gross_weight_kg": "98.0",
                },
                {
                    "sku": "TZF-VLV-CTRL",
                    "uom": "PCS",
                    "description": "[TZF-VLV-CTRL] Diaphragm Operated Pneumatic Valve Control Assembly with 4-20mA Feedback Sensor",
                    "hs_code": "84818099",
                    "quantity": "6",
                    "unit_price": "520.00",
                    "line_total": "3120.00",
                    "packages": "2 Cartons",
                    "net_weight_kg": "52.0",
                    "gross_weight_kg": "60.0",
                },
            ],
            "invoice_total": "5920.00",
        },
        {
            "shipment_number": "MKN-DEMO-013",
            "invoice_number": "INV-DEMO-MKN-013",
            "packing_list_number": "PKL-DEMO-MKN-013",
            "bl_number": "BL-DEMO-MKN-013",
            "status": "submitted",
            "supplier_name": "Kobe Industrial Pumps Co.",
            "supplier_email": "export@kobe-pumps.example",
            "origin_country": "JP",
            "currency": "USD",
            "exchange_rate_demo": "16200.00",
            "approval_notes": "DEMO fixture: PIB submitted with tax ID and billing code issued",
            "has_packing_list": True,
            "has_bl": True,
            "datasheet_code": None,
            "items": [
                {
                    "sku": "KIB-PMP-CENT",
                    "uom": "UNIT",
                    "description": "[KIB-PMP-CENT] Multi-Stage High Head Centrifugal Pump Set 11kW 380V Mechanical Seal SS316 Impeller",
                    "hs_code": "84137099",
                    "quantity": "2",
                    "unit_price": "3600.00",
                    "line_total": "7200.00",
                    "packages": "2 Crates",
                    "net_weight_kg": "460.0",
                    "gross_weight_kg": "530.0",
                },
                {
                    "sku": "KIB-FLT-WAT",
                    "uom": "SET",
                    "description": "[KIB-FLT-WAT] Ultrafiltration Membrane Industrial Water Filter Skid with Automated Backwash Valve",
                    "hs_code": "84212122",
                    "quantity": "1",
                    "unit_price": "5400.00",
                    "line_total": "5400.00",
                    "packages": "1 Crate",
                    "net_weight_kg": "380.0",
                    "gross_weight_kg": "440.0",
                },
            ],
            "invoice_total": "12600.00",
        },
        {
            "shipment_number": "MKN-DEMO-014",
            "invoice_number": "INV-DEMO-MKN-014",
            "packing_list_number": "PKL-DEMO-MKN-014",
            "bl_number": "BL-DEMO-MKN-014",
            "status": "arrived",
            "supplier_name": "Suzhou Cleanroom Garments Ltd.",
            "supplier_email": "contact@suzhou-garments.example",
            "origin_country": "CN",
            "currency": "USD",
            "exchange_rate_demo": "16200.00",
            "approval_notes": "DEMO fixture: goods received at PT Mitra Kemas Nusantara warehouse",
            "has_packing_list": True,
            "has_bl": True,
            "datasheet_code": None,
            "items": [
                {
                    "sku": "SZG-WRK-PNT",
                    "uom": "PCS",
                    "description": "[SZG-WRK-PNT] Heavy Industrial Work Trousers Multi-Pocket Cotton Canvas Anti-Static Treated",
                    "hs_code": "62034290",
                    "quantity": "150",
                    "unit_price": "16.00",
                    "line_total": "2400.00",
                    "packages": "6 Cartons",
                    "net_weight_kg": "120.0",
                    "gross_weight_kg": "135.0",
                },
                {
                    "sku": "SZG-WRK-TSH",
                    "uom": "PCS",
                    "description": "[SZG-WRK-TSH] Cotton Crew Neck Industrial Work Shirt 180gsm Colorfast Preshrunk Knitwear",
                    "hs_code": "61091010",
                    "quantity": "300",
                    "unit_price": "6.00",
                    "line_total": "1800.00",
                    "packages": "6 Cartons",
                    "net_weight_kg": "85.0",
                    "gross_weight_kg": "96.0",
                },
            ],
            "invoice_total": "4200.00",
        },
    ]

    datasheets = [
        {
            "code": "DS-APX-M8422",
            "file_name": "DS-APX-M8422.pdf",
            "title": "Technical Datasheet: Multi-Head Automatic Liquid Filling & Packaging Machine",
            "manufacturer": "Apex Automation Machinery Co., Ltd.",
            "model": "APX-M8422-FL / WR Series",
            "hs_reference": "84223000 / 84224000",
            "specs": [
                ("Filling Speed", "24 - 48 bottles/min (customizable multi-head nozzle)"),
                ("Dosing Range", "50ml - 1000ml volumetric piston dispenser"),
                ("Power Supply", "380V AC 3-Phase, 50Hz, Rated Power 2.2 kW"),
                ("Construction", "Stainless Steel SUS304 / Contact parts SUS316L"),
                ("Air Consumption", "0.6 - 0.8 MPa, 0.4 m3/min clean dry air"),
                ("Controller", "Siemens S7 PLC with 7-inch Color HMI Touchscreen"),
                ("Wrapping Module", "Thermal heat-shrink tunnel with PID digital temperature regulation"),
            ],
        },
        {
            "code": "DS-NFC-V8481",
            "file_name": "DS-NFC-V8481.pdf",
            "title": "Technical Datasheet: Industrial Pneumatic Control & Pressure Reducing Valves",
            "manufacturer": "Nordic Flow Controls AB",
            "model": "NFC-V8481 Series",
            "hs_reference": "84818099 / 84811099",
            "specs": [
                ("Nominal Pressure", "PN16 / ANSI Class 150"),
                ("Body Material", "Cast Stainless Steel CF8M (AISI 316)"),
                ("Seat Material", "Reinforced PTFE with Zero Leakage Class VI"),
                ("Actuator Type", "Spring-Return Pneumatic Diaphragm Actuator with 4-20mA Positioner"),
                ("Operating Temp", "-20 deg C to +180 deg C"),
                ("End Connection", "Flanged EN 1092-1 / Threaded BSP Female"),
            ],
        },
        {
            "code": "DS-DGM-MOT",
            "file_name": "DS-DGM-MOT.pdf",
            "title": "Technical Datasheet: Three-Phase Asynchronous Induction Motor",
            "manufacturer": "Dongguan Precision Motors Ltd.",
            "model": "DGM-MOT-3PH-1500",
            "hs_reference": "85015219",
            "specs": [
                ("Rated Power", "1.5 kW (2.0 HP) continuous duty S1"),
                ("Rated Voltage", "380V AC Delta / 660V Star, 50Hz"),
                ("Synchronous Speed", "1500 rpm (4-Pole), Full load speed 1420 rpm"),
                ("Enclosure & Protection", "IP55 Cast Iron TEFC (Totally Enclosed Fan Cooled)"),
                ("Insulation Class", "Class F (Temperature rise Class B 80K)"),
                ("Efficiency", "IE3 Premium Efficiency according to IEC 60034-30-1"),
            ],
        },
        {
            "code": "DS-BBI-OIL",
            "file_name": "DS-BBI-OIL.pdf",
            "title": "Technical Datasheet & Specification: Sandalwood Essential Oil",
            "manufacturer": "BioBotanica Ingredients Inc.",
            "model": "Pure Sandalwood Oil (Santalum album)",
            "hs_reference": "33012920",
            "specs": [
                ("Botanical Source", "Santalum album L. (Heartwood steam distilled)"),
                ("Appearance", "Pale yellow to golden viscous liquid"),
                ("Odor Profile", "Rich, sweet, warm-woody, balsamic aroma"),
                ("Specific Gravity", "0.965 - 0.980 at 20 deg C"),
                ("Refractive Index", "1.500 - 1.510 at 20 deg C"),
                ("Total Santalol Content", "Min. 90.0% (alpha-santalol + beta-santalol by GC-MS)"),
                ("Food/Cosmetic Grade", "Aroma raw material, IFRA 51st Amendment compliant"),
            ],
        },
        {
            "code": "DS-SPC-PLC",
            "file_name": "DS-SPC-PLC.pdf",
            "title": "Technical Datasheet: Industrial Automation Modular PLC Panel",
            "manufacturer": "Siemens Process Control AG",
            "model": "SIMATIC S7-1500 CPU 1515-2 PN",
            "hs_reference": "85371019",
            "specs": [
                ("CPU Processing Time", "30 ns for bit operations, 48 ns for word operations"),
                ("Work Memory", "500 KB code, 3 MB data"),
                ("Interfaces", "2x PROFINET IO IRT interfaces, integrated web server"),
                ("Digital I/O Expansion", "Up to 32 modules on central rack, Modbus RTU/TCP supported"),
                ("Supply Voltage", "24V DC (-15% / +20%) reverse polarity protected"),
                ("Operating Temp", "-25 deg C to +60 deg C horizontal installation"),
            ],
        },
    ]

    return {
        "is_fictional": True,
        "demonstration_notice": "FICTIONAL DEMO DATASET — FOR SYSTEM SIMULATION & ACCEPTANCE TESTING ONLY",
        "company_name": "PT Mitra Kemas Nusantara",
        "shipments": shipments_data,
        "datasheets": datasheets,
    }


def draw_watermark_callback(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica-Bold", 34)
    canvas.setFillColor(colors.HexColor("#DC2626"), alpha=0.13)
    canvas.translate(297, 420)
    canvas.rotate(45)
    canvas.drawCentredString(0, 20, "FICTIONAL DEMO ARTIFACT")
    canvas.drawCentredString(0, -25, "NOT A REAL CUSTOMS DOCUMENT")
    canvas.restoreState()


def generate_watermarked_invoice_pdf(shipment: dict, out_path: Path):
    doc = SimpleDocTemplate(
        str(out_path),
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "InvoiceTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#065F46"),
    )
    subtitle_style = ParagraphStyle(
        "InvoiceSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#4B5563"),
    )
    box_header_style = ParagraphStyle(
        "BoxHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#111827"),
    )
    box_body_style = ParagraphStyle(
        "BoxBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#374151"),
    )
    meta_label_style = ParagraphStyle(
        "MetaLabel",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#374151"),
    )
    meta_val_style = ParagraphStyle(
        "MetaVal",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#111827"),
    )
    th_style = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.white,
        alignment=1,
    )
    td_style = ParagraphStyle(
        "TableBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#1F2937"),
    )
    td_center_style = ParagraphStyle(
        "TableBodyCenter",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#1F2937"),
        alignment=1,
    )
    td_right_style = ParagraphStyle(
        "TableBodyRight",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#1F2937"),
        alignment=2,
    )
    total_label_style = ParagraphStyle(
        "TotalLabel",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#111827"),
        alignment=2,
    )
    total_val_style = ParagraphStyle(
        "TotalVal",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#065F46"),
        alignment=2,
    )
    footer_style = ParagraphStyle(
        "FooterNotice",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#DC2626"),
    )

    story = []

    story.append(Paragraph("COMMERCIAL INVOICE (DEMO)", title_style))
    story.append(Spacer(1, 2))
    story.append(Paragraph("FICTIONAL DEMO ARTIFACT — For software testing and pipeline validation only", subtitle_style))
    story.append(Spacer(1, 10))

    shipper_text = (
        f"<b>{shipment['supplier_name']}</b><br/>"
        f"Email: {shipment['supplier_email']}<br/>"
        f"Country of Origin: {shipment['origin_country']}"
    )
    consignee_text = (
        "<b>PT Mitra Kemas Nusantara</b><br/>"
        "Kawasan Industri MM2100, Cikarang Barat<br/>"
        "Bekasi, Jawa Barat - Indonesia<br/>"
        "NPWP: 01.234.567.8-411.000"
    )

    parties_data = [
        [Paragraph("Shipper / Exporter:", box_header_style), Paragraph("Consignee / Importer:", box_header_style)],
        [Paragraph(shipper_text, box_body_style), Paragraph(consignee_text, box_body_style)],
    ]
    parties_table = Table(parties_data, colWidths=[256, 256])
    parties_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F9FAFB")),
        ("BOX", (0, 0), (0, -1), 0.5, colors.HexColor("#D1D5DB")),
        ("BOX", (1, 0), (1, -1), 0.5, colors.HexColor("#D1D5DB")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(parties_table)
    story.append(Spacer(1, 8))

    meta_data = [
        [
            Paragraph("Invoice No:", meta_label_style),
            Paragraph(shipment["invoice_number"], meta_val_style),
            Paragraph("Shipment No:", meta_label_style),
            Paragraph(shipment["shipment_number"], meta_val_style),
        ],
        [
            Paragraph("Date:", meta_label_style),
            Paragraph("2026-11-04", meta_val_style),
            Paragraph("Terms:", meta_label_style),
            Paragraph("CIF Tanjung Priok", meta_val_style),
        ],
        [
            Paragraph("Currency:", meta_label_style),
            Paragraph(shipment["currency"], meta_val_style),
            Paragraph("Status:", meta_label_style),
            Paragraph(f"<b>{shipment['status'].upper()}</b>", meta_val_style),
        ],
    ]
    meta_table = Table(meta_data, colWidths=[70, 186, 80, 176])
    meta_table.setStyle(TableStyle([
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 10))

    table_rows = [
        [
            Paragraph("No", th_style),
            Paragraph("SKU", th_style),
            Paragraph("Description of Goods", th_style),
            Paragraph("HS Code", th_style),
            Paragraph("Qty / UOM", th_style),
            Paragraph("Price", th_style),
            Paragraph("Total", th_style),
        ]
    ]

    for idx, item in enumerate(shipment["items"], 1):
        uom_str = item.get("uom", "UNIT")
        item_desc = item["description"]
        table_rows.append([
            Paragraph(str(idx), td_center_style),
            Paragraph(item["sku"], td_style),
            Paragraph(item_desc, td_style),
            Paragraph(item["hs_code"], td_center_style),
            Paragraph(f"{item['quantity']} {uom_str}", td_center_style),
            Paragraph(f"${float(item['unit_price']):,.2f}", td_right_style),
            Paragraph(f"${float(item['line_total']):,.2f}", td_right_style),
        ])

    table_rows.append([
        Paragraph("Total Invoice Amount:", total_label_style),
        "", "", "", "", "",
        Paragraph(f"${float(shipment['invoice_total']):,.2f} {shipment['currency']}", total_val_style),
    ])

    items_table = Table(table_rows, colWidths=[20, 72, 204, 58, 48, 56, 65], repeatRows=1)
    items_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#065F46")),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -2), 0.5, colors.HexColor("#E5E7EB")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("SPAN", (0, -1), (5, -1)),
        ("LINEABOVE", (0, -1), (-1, -1), 1, colors.HexColor("#065F46")),
        ("TOPPADDING", (0, -1), (-1, -1), 6),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 6),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 14))

    story.append(Paragraph(
        "DISCLAIMER: This document is a synthetic demonstration artifact created strictly for software testing and validation.",
        footer_style,
    ))
    story.append(Paragraph(
        f"Approval State / Fixture Notes: {shipment['approval_notes']}",
        footer_style,
    ))

    doc.build(story, onFirstPage=draw_watermark_callback)


def generate_watermarked_packing_list_pdf(shipment: dict, out_path: Path):
    doc = SimpleDocTemplate(
        str(out_path),
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
    )
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "PLTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#047857"),
    )
    subtitle_style = ParagraphStyle(
        "PLSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#4B5563"),
    )
    box_header_style = ParagraphStyle(
        "BoxHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#111827"),
    )
    box_body_style = ParagraphStyle(
        "BoxBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#374151"),
    )
    meta_label_style = ParagraphStyle(
        "MetaLabel",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#374151"),
    )
    meta_val_style = ParagraphStyle(
        "MetaVal",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#111827"),
    )
    th_style = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.white,
        alignment=1,
    )
    td_style = ParagraphStyle(
        "TableBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#1F2937"),
    )
    td_center_style = ParagraphStyle(
        "TableBodyCenter",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#1F2937"),
        alignment=1,
    )
    td_right_style = ParagraphStyle(
        "TableBodyRight",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#1F2937"),
        alignment=2,
    )
    total_label_style = ParagraphStyle(
        "TotalLabel",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#111827"),
        alignment=2,
    )
    total_val_style = ParagraphStyle(
        "TotalVal",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#047857"),
        alignment=2,
    )
    footer_style = ParagraphStyle(
        "FooterNotice",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#DC2626"),
    )

    story = []
    story.append(Paragraph("PACKING LIST (DEMO)", title_style))
    story.append(Spacer(1, 2))
    story.append(Paragraph("FICTIONAL DEMO ARTIFACT — For software testing and pipeline validation only", subtitle_style))
    story.append(Spacer(1, 10))

    shipper_text = (
        f"<b>{shipment['supplier_name']}</b><br/>"
        f"Email: {shipment['supplier_email']}<br/>"
        f"Country of Origin: {shipment['origin_country']}"
    )
    consignee_text = (
        "<b>PT Mitra Kemas Nusantara</b><br/>"
        "Kawasan Industri MM2100, Cikarang Barat<br/>"
        "Bekasi, Jawa Barat - Indonesia<br/>"
        "NPWP: 01.234.567.8-411.000"
    )

    parties_data = [
        [Paragraph("Shipper / Exporter:", box_header_style), Paragraph("Consignee / Importer:", box_header_style)],
        [Paragraph(shipper_text, box_body_style), Paragraph(consignee_text, box_body_style)],
    ]
    parties_table = Table(parties_data, colWidths=[256, 256])
    parties_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F9FAFB")),
        ("BOX", (0, 0), (0, -1), 0.5, colors.HexColor("#D1D5DB")),
        ("BOX", (1, 0), (1, -1), 0.5, colors.HexColor("#D1D5DB")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(parties_table)
    story.append(Spacer(1, 8))

    meta_data = [
        [
            Paragraph("Packing List No:", meta_label_style),
            Paragraph(shipment["packing_list_number"], meta_val_style),
            Paragraph("Shipment No:", meta_label_style),
            Paragraph(shipment["shipment_number"], meta_val_style),
        ],
        [
            Paragraph("Invoice Ref:", meta_label_style),
            Paragraph(shipment["invoice_number"], meta_val_style),
            Paragraph("Date:", meta_label_style),
            Paragraph("2026-11-04", meta_val_style),
        ],
        [
            Paragraph("Port of Loading:", meta_label_style),
            Paragraph("Shanghai Port, CN" if shipment["origin_country"] == "CN" else "Main Port", meta_val_style),
            Paragraph("Port of Discharge:", meta_label_style),
            Paragraph("Tanjung Priok, Jakarta", meta_val_style),
        ],
    ]
    meta_table = Table(meta_data, colWidths=[80, 176, 80, 176])
    meta_table.setStyle(TableStyle([
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 10))

    table_rows = [
        [
            Paragraph("No", th_style),
            Paragraph("SKU", th_style),
            Paragraph("Description of Goods", th_style),
            Paragraph("Packages", th_style),
            Paragraph("Qty / UOM", th_style),
            Paragraph("Net Wt (kg)", th_style),
            Paragraph("Gross Wt (kg)", th_style),
        ]
    ]

    total_net = Decimal(0)
    total_gross = Decimal(0)

    for idx, item in enumerate(shipment["items"], 1):
        uom_str = item.get("uom", "UNIT")
        pkgs = item.get("packages", "1 Package")
        net_wt = Decimal(str(item.get("net_weight_kg", "100.0")))
        gross_wt = Decimal(str(item.get("gross_weight_kg", "120.0")))
        total_net += net_wt
        total_gross += gross_wt

        table_rows.append([
            Paragraph(str(idx), td_center_style),
            Paragraph(item["sku"], td_style),
            Paragraph(item["description"], td_style),
            Paragraph(pkgs, td_center_style),
            Paragraph(f"{item['quantity']} {uom_str}", td_center_style),
            Paragraph(f"{float(net_wt):,.1f}", td_right_style),
            Paragraph(f"{float(gross_wt):,.1f}", td_right_style),
        ])

    table_rows.append([
        Paragraph("Total Weights & Summary:", total_label_style),
        "", "", "", "",
        Paragraph(f"{float(total_net):,.1f} kg", total_val_style),
        Paragraph(f"{float(total_gross):,.1f} kg", total_val_style),
    ])

    items_table = Table(table_rows, colWidths=[20, 70, 195, 65, 53, 60, 60], repeatRows=1)
    items_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#047857")),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -2), 0.5, colors.HexColor("#E5E7EB")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("SPAN", (0, -1), (4, -1)),
        ("LINEABOVE", (0, -1), (-1, -1), 1, colors.HexColor("#047857")),
        ("TOPPADDING", (0, -1), (-1, -1), 6),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 6),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 14))

    story.append(Paragraph(
        "DISCLAIMER: This document is a synthetic demonstration artifact created strictly for software testing and validation.",
        footer_style,
    ))

    doc.build(story, onFirstPage=draw_watermark_callback)


def generate_watermarked_bill_of_lading_pdf(shipment: dict, out_path: Path):
    doc = SimpleDocTemplate(
        str(out_path),
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
    )
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "BLTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#1E3A8A"),
    )
    subtitle_style = ParagraphStyle(
        "BLSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#4B5563"),
    )
    box_header_style = ParagraphStyle(
        "BoxHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#111827"),
    )
    box_body_style = ParagraphStyle(
        "BoxBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#374151"),
    )
    meta_label_style = ParagraphStyle(
        "MetaLabel",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#374151"),
    )
    meta_val_style = ParagraphStyle(
        "MetaVal",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#111827"),
    )
    th_style = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.white,
        alignment=1,
    )
    td_style = ParagraphStyle(
        "TableBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#1F2937"),
    )
    td_center_style = ParagraphStyle(
        "TableBodyCenter",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#1F2937"),
        alignment=1,
    )
    td_right_style = ParagraphStyle(
        "TableBodyRight",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#1F2937"),
        alignment=2,
    )
    footer_style = ParagraphStyle(
        "FooterNotice",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#DC2626"),
    )

    story = []
    story.append(Paragraph("OCEAN BILL OF LADING (DEMO)", title_style))
    story.append(Spacer(1, 2))
    story.append(Paragraph("FICTIONAL DEMO ARTIFACT — Non-negotiable copy for software pipeline validation only", subtitle_style))
    story.append(Spacer(1, 10))

    shipper_text = (
        f"<b>{shipment['supplier_name']}</b><br/>"
        f"Email: {shipment['supplier_email']}<br/>"
        f"Country of Origin: {shipment['origin_country']}"
    )
    consignee_text = (
        "<b>PT Mitra Kemas Nusantara</b><br/>"
        "Kawasan Industri MM2100, Cikarang Barat<br/>"
        "Bekasi, Jawa Barat - Indonesia<br/>"
        "NPWP: 01.234.567.8-411.000"
    )

    parties_data = [
        [Paragraph("Shipper:", box_header_style), Paragraph("Consignee:", box_header_style)],
        [Paragraph(shipper_text, box_body_style), Paragraph(consignee_text, box_body_style)],
    ]
    parties_table = Table(parties_data, colWidths=[256, 256])
    parties_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F9FAFB")),
        ("BOX", (0, 0), (0, -1), 0.5, colors.HexColor("#D1D5DB")),
        ("BOX", (1, 0), (1, -1), 0.5, colors.HexColor("#D1D5DB")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(parties_table)
    story.append(Spacer(1, 8))

    meta_data = [
        [
            Paragraph("B/L Number:", meta_label_style),
            Paragraph(shipment["bl_number"], meta_val_style),
            Paragraph("Shipment No:", meta_label_style),
            Paragraph(shipment["shipment_number"], meta_val_style),
        ],
        [
            Paragraph("Ocean Vessel / Voyage:", meta_label_style),
            Paragraph("EVER LEADER V.024W", meta_val_style),
            Paragraph("Port of Loading:", meta_label_style),
            Paragraph("Shanghai Port, CN" if shipment["origin_country"] == "CN" else "Main Port", meta_val_style),
        ],
        [
            Paragraph("Port of Discharge:", meta_label_style),
            Paragraph("Tanjung Priok, Jakarta, ID", meta_val_style),
            Paragraph("Freight Terms:", meta_label_style),
            Paragraph("FREIGHT PREPAID", meta_val_style),
        ],
    ]
    meta_table = Table(meta_data, colWidths=[100, 156, 100, 156])
    meta_table.setStyle(TableStyle([
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 10))

    container_no = f"EMCU-{abs(hash(shipment['shipment_number'])) % 899999 + 100000}"
    seal_no = f"SL-{abs(hash(shipment['invoice_number'])) % 89999 + 10000}"

    table_rows = [
        [
            Paragraph("Container / Seal No", th_style),
            Paragraph("Marks & Numbers", th_style),
            Paragraph("Description of Packages & Goods", th_style),
            Paragraph("Gross Weight (kg)", th_style),
            Paragraph("Volume (CBM)", th_style),
        ]
    ]

    total_gross = sum(Decimal(str(item.get("gross_weight_kg", "100.0"))) for item in shipment["items"])
    item_summaries = "<br/>".join(f"- {it['description']} ({it['quantity']} {it.get('uom', 'UNIT')})" for it in shipment["items"])

    table_rows.append([
        Paragraph(f"<b>{container_no}</b><br/>Seal: {seal_no}<br/>1x40' High Cube", td_style),
        Paragraph("PT MKN<br/>JAKARTA<br/>C/NO. 1-UP", td_center_style),
        Paragraph(f"<b>SAID TO CONTAIN:</b><br/>{item_summaries}", td_style),
        Paragraph(f"{float(total_gross):,.1f} kg", td_right_style),
        Paragraph("28.5 CBM", td_right_style),
    ])

    items_table = Table(table_rows, colWidths=[105, 75, 202, 70, 70], repeatRows=1)
    items_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E3A8A")),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 14))

    story.append(Paragraph(
        "DISCLAIMER: This document is a synthetic demonstration artifact created strictly for software testing and validation.",
        footer_style,
    ))

    doc.build(story, onFirstPage=draw_watermark_callback)


def generate_watermarked_datasheet_pdf(ds: dict, out_path: Path):
    doc = SimpleDocTemplate(
        str(out_path),
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
    )
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "DSTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=20,
        textColor=colors.HexColor("#0F172A"),
    )
    subtitle_style = ParagraphStyle(
        "DSSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#4B5563"),
    )
    meta_label_style = ParagraphStyle(
        "MetaLabel",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#334155"),
    )
    meta_val_style = ParagraphStyle(
        "MetaVal",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#0F172A"),
    )
    th_style = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=colors.white,
        alignment=1,
    )
    td_style = ParagraphStyle(
        "TableBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#1E293B"),
    )
    td_bold_style = ParagraphStyle(
        "TableBodyBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#0F172A"),
    )
    footer_style = ParagraphStyle(
        "FooterNotice",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#DC2626"),
    )

    story = []
    story.append(Paragraph(ds["title"], title_style))
    story.append(Spacer(1, 2))
    story.append(Paragraph("FICTIONAL DEMO DATASHEET — Technical reference for classification and pipeline validation", subtitle_style))
    story.append(Spacer(1, 10))

    meta_data = [
        [
            Paragraph("Manufacturer:", meta_label_style),
            Paragraph(ds["manufacturer"], meta_val_style),
        ],
        [
            Paragraph("Model / Series:", meta_label_style),
            Paragraph(ds["model"], meta_val_style),
        ],
        [
            Paragraph("HS Code Reference:", meta_label_style),
            Paragraph(ds["hs_reference"], meta_val_style),
        ],
    ]
    meta_table = Table(meta_data, colWidths=[120, 403])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ("BOX", (0, 0), (0, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 10))

    spec_rows = [
        [
            Paragraph("Parameter / Specification Item", th_style),
            Paragraph("Engineering Details & Value", th_style),
        ]
    ]

    for param, val in ds["specs"]:
        spec_rows.append([
            Paragraph(param, td_bold_style),
            Paragraph(val, td_style),
        ])

    spec_table = Table(spec_rows, colWidths=[160, 363], repeatRows=1)
    spec_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(spec_table)
    story.append(Spacer(1, 14))

    story.append(Paragraph(
        "DISCLAIMER: This document is a synthetic demonstration artifact created strictly for software testing and validation.",
        footer_style,
    ))

    doc.build(story, onFirstPage=draw_watermark_callback)


def main():
    DATA_DEMO.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    data = build_shipments_dataset()
    json_path = DATA_DEMO / "shipments.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"Generated {json_path} with {len(data['shipments'])} shipments and {len(data.get('datasheets', []))} datasheets")

    # 1. Generate Commercial Invoices
    for s in data["shipments"]:
        inv_pdf = DOCS_DIR / f"{s['invoice_number']}.pdf"
        generate_watermarked_invoice_pdf(s, inv_pdf)

    # 2. Generate Packing Lists
    for s in data["shipments"]:
        if s.get("has_packing_list", True):
            pkl_pdf = DOCS_DIR / f"{s['packing_list_number']}.pdf"
            generate_watermarked_packing_list_pdf(s, pkl_pdf)

    # 3. Generate Bills of Lading
    for s in data["shipments"]:
        if s.get("has_bl", True):
            bl_pdf = DOCS_DIR / f"{s['bl_number']}.pdf"
            generate_watermarked_bill_of_lading_pdf(s, bl_pdf)

    # 4. Generate Datasheets
    for ds in data.get("datasheets", []):
        ds_pdf = DOCS_DIR / ds["file_name"]
        generate_watermarked_datasheet_pdf(ds, ds_pdf)

    print(f"Generated complete document set in {DOCS_DIR}")

    # Generate preview PNG from MKN-DEMO-001 using pdftoppm
    sample_shipment = data["shipments"][0]
    sample_pdf = DOCS_DIR / f"{sample_shipment['invoice_number']}.pdf"
    prefix = "/tmp/artha-demo-preview"
    cmd = ["pdftoppm", "-png", "-r", "150", "-singlefile", str(sample_pdf), prefix]
    subprocess.run(cmd, check=True)
    preview_png_tmp = Path(f"{prefix}.png")
    preview_png_dest = DOCS_DIR / "preview.png"
    if preview_png_tmp.exists():
        shutil.copyfile(preview_png_tmp, preview_png_dest)
        print(f"Generated preview PNG at {preview_png_tmp} and {preview_png_dest}")


if __name__ == "__main__":
    main()
