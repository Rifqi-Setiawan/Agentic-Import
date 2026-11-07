"""Shared lexical ranking over the canonical BTKI catalogue."""
import math
import re
from collections import Counter

from src.core.catalog import get_official_hs_code, is_official_hs_code

HS_SEARCH_COLUMNS = "hs_code,description_id,description_en,bm_rate,lartas_coverage,source"


def _stem(word: str) -> str:
    w = word.lower()
    if len(w) > 4 and w.endswith("ies"):
        return w[:-3] + "y"
    if len(w) > 4 and w.endswith("es") and (w.endswith("shes") or w.endswith("ches") or w.endswith("xes") or w.endswith("sses")):
        return w[:-2]
    if len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
        return w[:-1]
    return w


def _tokenize(text: str) -> set[str]:
    raw = re.findall(r"t-shirt|[a-z0-9]{3,}", (text or "").lower())
    return {_stem(w) for w in raw}


# Bilingual terminology across the catalogue's five chapters.
TERM_GROUPS = (
    "lipstik lipstick bibir lip",
    "parfum perfume wewangian fragrance",
    "sabun soap",
    "katun cotton kapas",
    "kaos t-shirt singlet oblong",
    "jaket jacket jas coat",
    "rajut knitted crocheted",
    "tenun woven",
    "katup valve kran tap",
    "searah nonreturn check",
    "besi iron",
    "baja steel",
    "cor cast tuang",
    "pompa pump",
    "sentrifugal centrifugal",
    "pengemas pembungkus packaging packing sealing penyegel",
    "listrik electric elektrik",
    "fase phase fasa",
    "sakelar switch sensor proximity",
    "baterai battery accumulator akumulator",
    "konektor connector plug soket socket",
    "transformator transformer trafo",
)
SYNONYMS_MAP = {
    _stem(term): {_stem(value) for value in group.split()}
    for group in TERM_GROUPS for term in group.split()
}

GENERIC_HEADING_TERMS = {
    "wire", "kabel", "kawat", "aparatu", "apparatus", "mesin", "machin",
    "part", "bagian", "articl", "barang", "other", "lain"
}

PHRASE_GROUPS = (
    (28, ("gate valve", "katup pintu", "katup gerbang")),
    (10, ("cast iron", "besi tuang", "besi cor")),
    (24, ("sealing machine", "mesin penyegel", "machinery for filling closing sealing")),
    (20, ("kaos", "t-shirt", "t shirt")),
    (20, ("motor listrik", "electric motor", "motor dan generator listrik")),
    (16, ("3 fase", "3 phase", "three phase", "tiga fase", "polyphase", "multi phase", "multifase")),
    (12, ("woven fabric", "kain tenun")),
    (20, ("toilet water", "eau de toilette")),
    (16, ("printed circuit", "sirkuit tercetak")),
)


def _phrase_text(text: str) -> str:
    return " " + " ".join(re.findall(r"[a-z0-9]+", text.lower())) + " "


def rank_hs_codes(rows, description: str, limit=8):
    # Normalized and canonical deduplication
    deduped_catalog = {}
    for r in rows:
        clean_code = str(r["hs_code"]).replace(".", "").strip()
        if is_official_hs_code(clean_code) and clean_code not in deduped_catalog:
            r_copy = dict(r)
            r_copy["hs_code"] = clean_code
            official = get_official_hs_code(clean_code)
            r_copy.update(description_id=official["description_id"], description_en=official["description_en"])
            deduped_catalog[clean_code] = r_copy

    if not deduped_catalog:
        return []

    desc_clean = (description or "").strip()
    if not desc_clean:
        return []

    # 1. Code-aware exact/prefix/dotted matching BEFORE lexical scoring
    digits_only = re.sub(r"[^0-9]", "", desc_clean)
    words = set(re.findall(r"[a-zA-Z]+", desc_clean.lower()))
    noise_code_words = {"hs", "code", "pos", "subpos", "nomor", "no", "kode", "chapter", "bab"}
    is_code_search = len(digits_only) >= 2 and (not words or words.issubset(noise_code_words))

    if is_code_search:
        code_matches = []
        for code, r in deduped_catalog.items():
            if code == digits_only:
                code_matches.append((1000.0, code, r))
            elif code.startswith(digits_only):
                code_matches.append((100.0, code, r))
        if code_matches:
            code_matches.sort(key=lambda x: (-x[0], x[1]))
            return [item[2] for item in code_matches[:limit]]
        return []

    num_docs = len(deduped_catalog)
    doc_data = []
    df = Counter()
    for code, r in deduped_catalog.items():
        segs_id = [s.strip() for s in r["description_id"].split("|")]
        segs_en = [s.strip() for s in (r.get("description_en") or "").split("|")]

        h_toks = _tokenize((segs_id[0] if segs_id else "") + " " + (segs_en[0] if segs_en else ""))
        sub_toks = _tokenize(" ".join(segs_id[1:2]) + " " + " ".join(segs_en[1:2]))
        leaf_toks = _tokenize(" ".join(segs_id[2:]) + " " + " ".join(segs_en[2:]))
        if not leaf_toks:
            leaf_toks = sub_toks

        all_toks = h_toks | sub_toks | leaf_toks
        for t in all_toks:
            df[t] += 1
        doc_data.append((code, r, h_toks, sub_toks, leaf_toks))

    def idf(term: str) -> float:
        freq = df.get(term, 0)
        return math.log(1 + (num_docs - freq + 0.5) / (freq + 0.5))

    stemmed_q = _tokenize(description)
    query_text = _phrase_text(description)
    active_phrases = [
        (weight, tuple(_phrase_text(phrase) for phrase in group))
        for weight, group in PHRASE_GROUPS
        if any(_phrase_text(phrase) in query_text or _phrase_text(phrase + "s") in query_text for phrase in group)
    ]

    query_weights: dict[str, float] = {}
    for w in stemmed_q:
        query_weights[w] = 1.0
        if w in SYNONYMS_MAP:
            for syn in SYNONYMS_MAP[w]:
                st = _stem(syn)
                query_weights.setdefault(st, 0.55)

    scored = []
    for code, r, h_toks, sub_toks, leaf_toks in doc_data:
        score = 0.0
        matches = 0
        for term, weight in sorted(query_weights.items()):
            term_idf = idf(term)
            if term_idf <= 0:
                continue

            matched = False
            if term in leaf_toks:
                score += 3.5 * term_idf * weight
                matched = True
            elif term in sub_toks:
                score += 2.5 * term_idf * weight
                matched = True
            elif term in h_toks:
                if term in GENERIC_HEADING_TERMS:
                    score += 0.1 * term_idf * weight
                else:
                    score += 1.0 * term_idf * weight
                matched = True

            if matched:
                matches += 1

        if active_phrases:
            catalogue_text = _phrase_text(r["description_id"] + " " + r["description_en"])
            heading_text = _phrase_text(r["description_id"].split("|", 1)[0] + " " + r["description_en"].split("|", 1)[0])
            for weight, group in active_phrases:
                if any(phrase in catalogue_text or phrase.rstrip() + "s " in catalogue_text for phrase in group):
                    score += weight
                    if any(phrase in heading_text or phrase.rstrip() + "s " in heading_text for phrase in group):
                        score += weight / 2
        if not score:
            continue

        if matches > 1:
            score *= (1.0 + 0.25 * (matches - 1))

        # Tie-breaker / general basket boost: only if matches > 0
        if code.endswith("99"):
            score += 0.05
        elif code.endswith("90"):
            score += 0.03

        if score > 0:
            scored.append((score, code, r))

    scored.sort(key=lambda x: (-x[0], x[1]))
    return [item[2] for item in scored[:limit]]
