#!/usr/bin/env python3
"""
HS Code Evaluation Runner for ImporJaga (MVP v1.1)
Reproducibly evaluates top-1 HS6, top-1 HS8, and top-3 HS8 accuracy.
Remediates Audit Finding F02.
"""
import sys
import json
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
    report_file = Path("reports/eval_report_agent.json")
    if not report_file.exists():
        print(f"Error: {report_file} does not exist", file=sys.stderr)
        sys.exit(1)

    data = json.loads(report_file.read_text(encoding="utf-8"))
    samples = data.get("samples", [])
    metrics = calculate_metrics(samples)
    print("Evaluation Results:", json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
