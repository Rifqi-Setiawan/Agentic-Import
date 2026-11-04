import hashlib
import json
import re
from pathlib import Path
import pypdf

ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = ROOT / "data" / "raw"
DATA_REF = ROOT / "data" / "reference"

URLS = {
    "33": "https://repository.beacukai.go.id/download/2022/03/37dcadbb1367deadc70a9fbea128a6aa-chapter-33.pdf",
    "61": "https://repository.beacukai.go.id/download/2022/03/bfa9ad80ffe304776378cd2310364dad-chapter-61.pdf",
    "62": "https://repository.beacukai.go.id/download/2022/03/aab1000c00b67cb7c231e11c3a281074-chapter-62.pdf",
    "84": "https://repository.beacukai.go.id/download/2022/03/3b564ac9fa2e6ee3ec10d87b59f3e9c0-chapter-84.pdf",
    "85": "https://repository.beacukai.go.id/download/2022/03/a9e033e776c2f740a53f5d005de0c727-chapter-85.pdf",
}


def parse_level_and_clean(t: str) -> tuple[int, str]:
    m = re.match(r"^(?:-\s*)+", t)
    if m:
        level = m.group(0).count("-")
        clean = t[m.end():].strip()
    else:
        level = 0
        clean = t.strip()
    clean = re.sub(r"\s*:\s*$", "", clean)
    return level, clean


def extract_chapter(ch: str) -> list[dict]:
    pdf_path = DATA_RAW / f"chapter-{ch}.pdf"
    if not pdf_path.exists():
        raise FileNotFoundError(f"Missing {pdf_path}")

    sha256 = hashlib.sha256(pdf_path.read_bytes()).hexdigest()
    url = URLS[ch]
    reader = pypdf.PdfReader(str(pdf_path))

    all_rows = []
    for p_idx, page in enumerate(reader.pages):
        page_num = p_idx + 1
        fragments = []

        def visitor(text, cm, tm, font_dict, font_size, target_list=fragments):
            t = text.strip()
            if t and "Pos Tarif" not in t and "Uraian Barang" not in t and "HS Code" not in t and "Description of Goods" not in t:
                target_list.append((round(tm[5], 1), round(tm[4], 1), text))

        page.extract_text(visitor_text=visitor)
        fragments.sort(key=lambda f: (f[0], f[1]))

        lines = []
        curr_y = None
        curr_line = []
        for y, x, t in fragments:
            if curr_y is None or abs(y - curr_y) > 3.0:
                if curr_line:
                    lines.append((curr_y, curr_line))
                curr_y = y
                curr_line = [(x, t)]
            else:
                curr_line.append((x, t))
        if curr_line:
            lines.append((curr_y, curr_line))

        for y, line in lines:
            code_txt = "".join(t for x, t in line if x < 150).strip()
            id_txt = "".join(t for x, t in line if 150 <= x < 550).strip()
            en_txt = "".join(t for x, t in line if x >= 550).strip()

            m_h4 = re.match(r"^(\d{2}\.\d{2})\s*(.*)$", code_txt)
            if m_h4:
                h_code = m_h4.group(1)
                h_extra = m_h4.group(2).strip()
                if h_extra:
                    id_txt = (h_extra + " " + id_txt).strip()
                code_txt = h_code

            all_rows.append((page_num, y, code_txt, id_txt, en_txt))

    logical_entries = []
    for p_num, _y, c_txt, id_txt, en_txt in all_rows:
        c_clean = re.sub(r"[^0-9.]", "", c_txt)
        if c_clean:
            logical_entries.append({
                "page": p_num,
                "code_raw": c_clean,
                "id_parts": [id_txt] if id_txt else [],
                "en_parts": [en_txt] if en_txt else []
            })
        else:
            if logical_entries:
                if id_txt:
                    logical_entries[-1]["id_parts"].append(id_txt)
                if en_txt:
                    logical_entries[-1]["en_parts"].append(en_txt)

    stack_id: dict[int, str] = {}
    stack_en: dict[int, str] = {}
    chapter_codes: list[dict] = []

    for entry in logical_entries:
        code_digits = entry["code_raw"].replace(".", "")
        id_full = " ".join(entry["id_parts"]).strip()
        en_full = " ".join(entry["en_parts"]).strip()

        lvl_id, clean_id = parse_level_and_clean(id_full)
        lvl_en, clean_en = parse_level_and_clean(en_full)
        level = max(lvl_id, lvl_en)

        if len(code_digits) == 4:
            level = 0
            stack_id.clear()
            stack_en.clear()

        stack_id = {k: v for k, v in stack_id.items() if k < level}
        stack_en = {k: v for k, v in stack_en.items() if k < level}

        if clean_id:
            stack_id[level] = clean_id
        if clean_en:
            stack_en[level] = clean_en

        if len(code_digits) == 8 and code_digits.isdigit():
            ctx_id = " | ".join(stack_id[k] for k in sorted(stack_id.keys()))
            ctx_en = " | ".join(stack_en[k] for k in sorted(stack_en.keys()))
            chapter_codes.append({
                "code": code_digits,
                "description_id": ctx_id or clean_id,
                "description_en": ctx_en or clean_en,
                "source_url": url,
                "source_page": entry["page"],
                "source_sha256": sha256,
                "lartas_verified": False,
                "current_rates_verified": False,
            })

    return chapter_codes


def main():
    DATA_REF.mkdir(parents=True, exist_ok=True)
    all_codes = []
    counts = {}

    for ch in ["33", "61", "62", "84", "85"]:
        codes = extract_chapter(ch)
        counts[ch] = len(codes)
        all_codes.extend(codes)

    print(f"Extracted codes per chapter: {counts}")
    print(f"Total extracted: {len(all_codes)}")

    # Deduplicate keeping first occurrence by code
    deduped = {}
    for item in all_codes:
        if item["code"] not in deduped:
            deduped[item["code"]] = item

    sorted_codes = sorted(deduped.values(), key=lambda x: x["code"])
    print(f"Total unique 8-digit codes: {len(sorted_codes)}")

    catalog = {
        "edition": "BTKI 2022",
        "consolidated_current": False,
        "source_note": "DJBC BTKI 2022 official PDF extracts (Chapters 33, 61, 62, 84, 85)",
        "codes": sorted_codes,
    }

    out_file = DATA_REF / "hs_codes_btki2022.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)

    print(f"Saved catalog to {out_file} ({out_file.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
