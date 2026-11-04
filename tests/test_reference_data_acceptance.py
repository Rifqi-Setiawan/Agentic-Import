"""Acceptance authored before implementation: source integrity and honest demo data."""
import json
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]


def dataset(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_official_catalog_has_unique_eight_digit_codes_and_traceable_pages():
    data = dataset("data/reference/hs_codes_btki2022.json")
    assert data["edition"] == "BTKI 2022"
    assert data["consolidated_current"] is False
    codes = data["codes"]
    assert len(codes) >= 1500
    assert len({r["code"] for r in codes}) == len(codes)
    assert {r["code"][:2] for r in codes} == {"33", "61", "62", "84", "85"}
    for row in codes:
        assert len(row["code"]) == 8 and row["code"].isdigit()
        assert row["description_id"].strip() and row["description_en"].strip()
        assert urlparse(row["source_url"]).hostname == "repository.beacukai.go.id"
        assert isinstance(row["source_page"], int) and row["source_page"] > 0
        assert len(row["source_sha256"]) == 64
        assert row.get("lartas_verified", False) is False
        assert row.get("current_rates_verified", False) is False


def test_reference_correction_is_from_official_chapter_33_not_legacy_guess():
    rows = {r["code"]: r for r in dataset("data/reference/hs_codes_btki2022.json")["codes"]}
    assert "cendana" in rows["33012920"]["description_id"].lower()
    assert "citronella" in rows["33012930"]["description_en"].lower()
    assert "nilam" in rows["33012960"]["description_id"].lower()
    assert "33012910" not in rows
    assert "84224000" in rows and "85365099" in rows


def test_real_regulation_library_has_direct_primary_sources_and_no_executable_guess():
    rows = dataset("data/reference/regulations.json")["references"]
    assert len(rows) >= 5
    assert len({r["number"] for r in rows}) == len(rows)
    assert any("68" in r["number"] and "2026" in r["number"] for r in rows)
    for row in rows:
        assert urlparse(row["source_url"]).hostname == "jdih.kemenkeu.go.id"
        assert "/dok/" in row["source_url"] and row["title"]
        assert row["reference_only"] is True
        assert row["verified_on"]


def test_demo_shipments_use_valid_references_and_honest_balanced_invoice_lines():
    data = dataset("data/demo/shipments.json")
    assert data["is_fictional"] is True
    catalog = {r["code"] for r in dataset("data/reference/hs_codes_btki2022.json")["codes"]}
    rows = data["shipments"]
    assert len(rows) >= 12
    assert len({r["shipment_number"] for r in rows}) == len(rows)
    assert len({r["invoice_number"] for r in rows}) == len(rows)
    assert sum(len(r["items"]) for r in rows) >= 24
    assert {"draft", "needs_clarification", "needs_review", "needs_documents", "ready", "submitted", "arrived"} <= {r["status"] for r in rows}
    for shipment in rows:
        assert shipment["supplier_email"].endswith(".example")
        assert "DEMO" in shipment["invoice_number"]
        assert Decimal(str(shipment["exchange_rate_demo"])) > 0
        amount = Decimal(0)
        for item in shipment["items"]:
            assert item["hs_code"] in catalog and item["sku"] and item["description"]
            assert Decimal(str(item["quantity"])) > 0
            assert Decimal(str(item["unit_price"])) > 0
            calculated = Decimal(str(item["quantity"])) * Decimal(str(item["unit_price"]))
            assert calculated == Decimal(str(item["line_total"])), item
            amount += calculated
        assert amount == Decimal(str(shipment["invoice_total"])), shipment
