"""Source-backed rates for the explicitly covered demo tariff lines."""
import csv
from decimal import Decimal
from functools import lru_cache

from src.core.config import PROJECT_ROOT

PPN_SOURCE = "https://jdih.kemenkeu.go.id/dok/pmk-131-tahun-2024"
PPH_SOURCE = "https://jdih.kemenkeu.go.id/dok/pmk-51-tahun-2025"


@lru_cache(maxsize=1)
def demo_rates():
    with (PROJECT_ROOT / "data/seed/rates_verified.csv").open(encoding="utf-8", newline="") as stream:
        return {row["hs_code"]: row for row in csv.DictReader(stream)}


def verified_demo_rate(code, bm_rate):
    row = demo_rates().get(code)
    return row if row and bm_rate is not None and Decimal(row["bm_rate"]) == bm_rate else None


def pph22_rate(has_api: bool, annex_rate: Decimal | None = None) -> tuple[Decimal, str]:
    if annex_rate is not None:
        return annex_rate, "lampiran"
    return (Decimal("2.5"), "with_api") if has_api else (Decimal("7.5"), "without_api")
