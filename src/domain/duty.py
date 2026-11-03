import math
from decimal import Decimal

from pydantic import BaseModel


class DutyInput(BaseModel):
    cif_idr: Decimal
    bm_percentage: Decimal = Decimal("5.0")
    ppn_percentage: Decimal = Decimal("11.0")
    pph_percentage: Decimal = Decimal("2.5")


class DutyOutput(BaseModel):
    cif_idr: Decimal
    bm_idr: Decimal
    nilai_impor_idr: Decimal
    ppn_idr: Decimal
    pph_idr: Decimal
    total_duties_idr: Decimal


def ceil_thousand(val: Decimal) -> Decimal:
    """
    Round up to nearest thousand (kebijakan pembulatan ke atas ribuan kepabeanan estimasi).
    """
    f_val = float(val)
    rounded = math.ceil(f_val / 1000.0) * 1000
    return Decimal(str(int(rounded)))


def calculate_import_duties(duty_input: DutyInput) -> DutyOutput:
    """
    Deterministic import duty calculations matching docs/MVP-v1.1.md:
    CIF Rp78.940.712,50 × 5% dibulatkan ke atas ribuan menghasilkan BM Rp3.948.000.
    Nilai impor: CIF + BM = Rp82.888.712,50.
    PPN 11% dibulatkan ke atas ribuan = Rp9.118.000.
    PPh 2,5% dibulatkan ke atas ribuan = Rp2.073.000.
    Total pungutan = Rp15.139.000.
    """
    # 1. Bea Masuk (BM)
    raw_bm = duty_input.cif_idr * (duty_input.bm_percentage / Decimal(100))
    bm_idr = ceil_thousand(raw_bm)

    # 2. Nilai Impor
    nilai_impor_idr = duty_input.cif_idr + bm_idr

    # 3. PPN
    raw_ppn = nilai_impor_idr * (duty_input.ppn_percentage / Decimal(100))
    ppn_idr = ceil_thousand(raw_ppn)

    # 4. PPh
    raw_pph = nilai_impor_idr * (duty_input.pph_percentage / Decimal(100))
    pph_idr = ceil_thousand(raw_pph)

    # 5. Total
    total_duties_idr = bm_idr + ppn_idr + pph_idr

    return DutyOutput(
        cif_idr=duty_input.cif_idr,
        bm_idr=bm_idr,
        nilai_impor_idr=nilai_impor_idr,
        ppn_idr=ppn_idr,
        pph_idr=pph_idr,
        total_duties_idr=total_duties_idr,
    )
