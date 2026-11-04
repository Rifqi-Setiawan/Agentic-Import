# Artha Reference Catalog & Regulations Library

## 1. BTKI 2022 Reference Catalog (`hs_codes_btki2022.json`)
- **Source**: Direktorat Jenderal Bea dan Cukai (DJBC) official chapter PDFs (2022 edition).
- **Scope**: 2,614 unique 8-digit codes across 5 key industrial chapters:
  - Chapter 33: 50 codes (Essential oils & resinoids; perfumery, cosmetic or toilet preparations)
  - Chapter 61: 131 codes (Articles of apparel and clothing accessories, knitted or crocheted)
  - Chapter 62: 221 codes (Articles of apparel and clothing accessories, not knitted or crocheted)
  - Chapter 84: 1,316 codes (Nuclear reactors, boilers, machinery and mechanical appliances)
  - Chapter 85: 896 codes (Electrical machinery and equipment and parts thereof)
- **Provenance**: Extracted directly via `pypdf` layout mode preserving Indonesian and English descriptions with full heading/subheading context. Every record tracks `source_url`, `source_page`, and `source_sha256`.
- **Mandatory Corrections**:
  - `33012920`: Minyak atsiri dari cendana / sandalwood oil (corrected from legacy misalignment).
  - `33012930`: Dari serai / citronella.
  - `33012960`: Dari nilam / patchouli.
  - `33012910`: Invalid code, verified absent from official DJBC BTKI 2022.
  - `84224000` & `85365099`: Verified present.
- **Tariff & Lartas Honesty**: Official DJBC PDFs publish nomenclature only (no binding duty rates or import permits). Metadata explicitly declares `consolidated_current: false`, `current_rates_verified: false`, and `lartas_verified: false`. Rates in pipeline are treated as `NULL` / `demo_unverified` with blocking compliance checklists.

## 2. Regulations Library (`regulations.json`)
- **Source**: JDIH Kementerian Keuangan RI (`jdih.kemenkeu.go.id`).
- **Records**: 5 verified primary decree references:
  - `PMK 26/PMK.010/2022`: Penetapan Sistem Klasifikasi Barang dan Pembebanan Tarif Bea Masuk atas Barang Impor
  - `PMK 10 TAHUN 2024`: Perubahan atas PMK 26/PMK.010/2022
  - `PMK 62 TAHUN 2025`: Perubahan Kedua atas PMK 26/PMK.010/2022
  - `PMK 50 TAHUN 2026`: Perubahan Ketiga atas PMK 26/PMK.010/2022
  - `PMK 68 TAHUN 2026`: Perubahan Keempat atas PMK 26/PMK.010/2022
- **Contract**: All entries tagged `reference_only: true` and `verified_on: "2026-11-04"`.

## 3. Demo Fixtures & Watermarked Documents (`data/demo/`)
- **Shipments**: 14 shipments, 28 items (`data/demo/shipments.json`).
  - Target company: PT Mitra Kemas Nusantara.
  - All 7 lifecycle statuses represented: `draft`, `needs_clarification`, `needs_review`, `needs_documents`, `ready`, `submitted`, `arrived`.
  - Exact Decimal arithmetic: `quantity * unit_price == line_total`, `sum(line_total) == invoice_total`.
  - Realistic SKU, UOM (`UNIT`, `SET`, `PCS`, `KG`), and industrial specifications.
- **Documents**: 41 ReportLab-generated watermarked synthetic PDFs in `data/demo/documents/`:
  - 14 Commercial Invoices (`INV-DEMO-MKN-*.pdf`)
  - 11 Packing Lists (`PKL-DEMO-MKN-*.pdf`)
  - 10 Bills of Lading (`BL-DEMO-MKN-*.pdf`)
  - 5 Technical Datasheets (`DS-*.pdf`)
  - 1 Representative Preview PNG (`preview.png`)

## 4. Additive Importer CLI (`scripts/import_reference_catalog.py`)
- **Safety**:
  - Test database guard enforces `current_database() == 'imporjaga_test'`.
  - Live deployment guard enforces `--live --apply` flags and verifies `current_database() == 'imporjaga'`.
  - Additive & idempotent: preserves reviewer human edits, skips existing scenarios, never deletes human classification memory.

### CLI Usage Commands
```bash
# 1. Test database import (default / test environment)
.venv/bin/python scripts/import_reference_catalog.py --company-id <COMPANY_ID>

# 2. Live production apply (Parent authorized operator only)
.venv/bin/python scripts/import_reference_catalog.py --company-id 1 --live --apply
```
