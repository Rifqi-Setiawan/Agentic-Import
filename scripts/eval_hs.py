#!/usr/bin/env python3
"""
HS Code Evaluation Runner for ImporJaga (MVP v1.1)
Reproducibly evaluates top-1 HS6, top-1 HS8, and top-3 HS8 accuracy.
Remediates Audit Finding F02.
"""
import argparse
import csv
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path


def calculate_metrics(predictions: list[dict]) -> dict:
    """
    Calculate exact accuracy metrics from raw predictions.
    All summary statistics are strictly derived from prediction outcomes.
    """
    total = len(predictions)
    if total == 0:
        return {
            "total_samples": 0,
            "top1_hs6_accuracy": 0.0,
            "top1_hs8_accuracy": 0.0,
            "top3_hs8_recall": 0.0,
        }

    hs6_correct = 0
    hs8_correct = 0
    top3_correct = 0

    for item in predictions:
        expected = item.get("expected_hs8", "").replace(".", "").strip()
        predicted = item.get("predicted_hs8", "").replace(".", "").strip()
        top_candidates = [c.replace(".", "").strip() for c in item.get("top_candidates", [])]

        # HS6 check (first 6 digits)
        if len(expected) >= 6 and len(predicted) >= 6 and expected[:6] == predicted[:6]:
            hs6_correct += 1

        # HS8 check (exact 8 digits)
        if len(expected) >= 8 and expected[:8] == predicted[:8]:
            hs8_correct += 1

        # Top 3 check
        if expected[:8] in top_candidates[:3]:
            top3_correct += 1

    return {
        "total_samples": total,
        "top1_hs6_accuracy": round(hs6_correct / total * 100, 2),
        "top1_hs8_accuracy": round(hs8_correct / total * 100, 2),
        "top3_hs8_recall": round(top3_correct / total * 100, 2),
        "hs6_correct": hs6_correct,
        "hs8_correct": hs8_correct,
        "top3_correct": top3_correct,
    }


def main():
    from src.core.catalog import CATALOG_PATH, get_official_catalog
    from src.core.config import settings
    from src.services.analysis import PROMPT_VERSION, classify_one
    from src.services.hs_search import rank_hs_codes

    parser = argparse.ArgumentParser(description="Evaluate the actual Artha catalogue and classifier.")
    parser.add_argument("--mode", choices=("retrieval_only", "agent"), required=True)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--dataset", default=Path("data/eval/eval_hs.csv"), type=Path)
    args = parser.parse_args()
    if args.mode == "agent" and not settings.LLM_MODEL:
        parser.error("Set LLM_MODEL to an authorized evaluation model.")

    catalogue = get_official_catalog()
    rows = [{"hs_code": code, "description_id": item["description_id"], "description_en": item["description_en"],
             "source": item["source_url"], "bm_rate": None, "lartas_coverage": "unknown"}
            for code, item in sorted(catalogue.items())]

    class EvaluationRepository:
        scope = (0, 0)
        company_id = run_id = 0

        def __init__(self):
            self.usage = 0

        def rows(self, sql, params=()):
            return rows if "FROM hs_codes" in sql else []

        def one(self, sql, params=()):
            return {"total_tokens": self.usage, "n": 1}

        def record_usage(self, response):
            self.usage += response.get("total_tokens") or 0

        def trace(self, *args):
            pass

        def questions(self, item_id):
            return []

    samples, excluded = [], []
    with args.dataset.open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            expected = row["expected_hs8"].replace(".", "").strip()
            if expected not in catalogue:
                excluded.append({"id": row["id"], "expected_hs8": expected, "reason": "label absent from catalogue"})
                continue
            ranked = rank_hs_codes(rows, row["description"], limit=10)
            candidates = [entry["hs_code"] for entry in ranked]
            repo = EvaluationRepository()
            if args.mode == "agent":
                decision = classify_one(repo, {"id": 0, "line_no": 1, "description": row["description"]}, [], {})
                predicted = decision.get("hs_code", "")
                top = [predicted, *(a["hs_code"] for a in decision.get("alternatives", []))] if predicted else []
                action = decision["action"]
            else:
                predicted = candidates[0] if candidates else ""
                top = candidates
                action = "retrieval"
            samples.append({"id": row["id"], "difficulty": row["difficulty"], "expected_hs8": expected,
                            "predicted_hs8": predicted, "top_candidates": top, "retrieval_candidates": candidates,
                            "action": action, "tokens": repo.usage if args.mode == "agent" else None})

    metrics = calculate_metrics(samples)
    metrics["retrieval_recall_at_10"] = round(100 * sum(
        sample["expected_hs8"] in sample["retrieval_candidates"] for sample in samples
    ) / len(samples), 2) if samples else None
    difficult = [sample for sample in samples if sample["difficulty"] == "hard"]
    metrics["hard_clarification_percentage"] = round(
        100 * sum(sample["action"] == "question" for sample in difficult) / len(difficult), 2
    ) if difficult and args.mode == "agent" else None
    report = {
        "mode": args.mode, "created_at": datetime.now(UTC).isoformat(), "prompt_version": PROMPT_VERSION,
        "model": settings.LLM_MODEL if args.mode == "agent" else None,
        "catalogue_sha256": hashlib.sha256(CATALOG_PATH.read_bytes()).hexdigest(),
        "dataset_sha256": hashlib.sha256(args.dataset.read_bytes()).hexdigest(),
        "label_status": "internal unverified labels; not an independent accuracy benchmark",
        "metrics": metrics, "excluded": excluded, "samples": samples,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
