#!/usr/bin/env python3
"""Experiment 2: Per-Rubric Agreement Analysis (from combined CSV).

Reads the 96,000-row combined four-judge CSV and computes:
  - Mean pairwise agreement (%) per rubric
  - Agreement class distribution (fully_agree / majority_agree / split / full_disagree)
  - Per-question, per-rubric judge scores and rationales

No LLM calls — purely analytical from the existing CSV.

Usage:
    python bigdata_1000/experiments/exp2_agreement_from_csv.py

Output:
    bigdata_1000/results/exp2_agreement_results.json
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent.parent
BIGDATA_DIR = Path(__file__).resolve().parent.parent

DATASET_PATH = ROOT / "benchmark_dataset" / "1000_questions_dataset.csv"
COMBINED_CSV = Path(
    "/Users/mahindragupthakotha/Downloads/judge_outputs/"
    "bigdata_four_model_review/all_four_judges_item_scores_bigdata_valid_only.csv"
)
OUTPUT_PATH = BIGDATA_DIR / "results" / "exp2_agreement_results.json"

JUDGES = ["biomistral", "medgemma", "meditron", "medalpaca"]
# The combined CSV uses "judge_name" not "judge_id"
JUDGE_COL = "judge_name"

# Per-rubric max_k values (maximum achievable score for normalization)
# Binary: max_k = 1.  Likert 1-5: max_k = 5.
RUBRIC_MAX_K = {
    "rubric1_pemat": 1,
    "rubric2_healthbench": 1,
    "rubric3_clinical_eval": 5,
    "rubric4_prometheus": 5,
    "rubric5_pemat_likert": 5,
}


def parse_score(x):
    """Parse a score value to float, or return None if unparseable."""
    if pd.isna(x):
        return None
    s = str(x).strip().upper()
    if s in {"NA", "N/A", "NONE", ""}:
        return None
    try:
        return float(s)
    except Exception:
        return None


def pairwise_agreement(scores_a: Dict[str, Any], scores_b: Dict[str, Any], rubric_id: str) -> float | None:
    """Paper Eq.1 per-pair agreement: 1 - (1/|R|) * sum_k (|s_i^k - s_j^k| / max_k).

    For binary rubrics (max_k=1), this reduces to exact-match agreement.
    For Likert rubrics (max_k=5), nearby scores get partial credit.
    """
    common_items = sorted(set(scores_a.keys()) & set(scores_b.keys()))
    if not common_items:
        return None

    max_k = RUBRIC_MAX_K.get(rubric_id, 5)
    total_diff = 0.0
    count = 0
    for item_id in common_items:
        a = parse_score(scores_a[item_id])
        b = parse_score(scores_b[item_id])
        if a is None or b is None:
            continue
        total_diff += abs(a - b) / max_k
        count += 1

    if count == 0:
        return None
    return 1.0 - total_diff / count


def classify_panel(pairwise_scores: List[float | None], threshold: float = 0.8) -> str:
    valid = [x for x in pairwise_scores if x is not None]
    if len(valid) < 3:
        return "skipped"
    n_good = sum(x >= threshold for x in valid)
    if n_good == len(valid):
        return "fully_agree"
    if n_good >= 3:
        return "majority_agree"
    if n_good == 0:
        return "full_disagree"
    return "split"


def build_item_scores(panel_df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    judge_item_scores = {}
    for judge_name, gdf in panel_df.groupby(JUDGE_COL):
        item_scores = {}
        for _, row in gdf.iterrows():
            item_id = row["item_id"]
            if pd.isna(item_id):
                continue
            item_scores[str(item_id)] = row.get("score")
        judge_item_scores[judge_name] = item_scores
    return judge_item_scores


def main():
    print("=" * 70)
    print("Experiment 2: Per-Rubric Agreement Analysis (from combined CSV)")
    print(f"Dataset:     {DATASET_PATH}")
    print(f"Combined CSV: {COMBINED_CSV}")
    print(f"Judges:      {JUDGES}")
    print("=" * 70)

    dataset_df = pd.read_csv(DATASET_PATH, low_memory=False)
    all_df = pd.read_csv(COMBINED_CSV, low_memory=False)

    all_df = all_df.copy()
    all_df["question_id"] = pd.to_numeric(all_df["question_id"], errors="coerce")
    all_df["rubric_id"] = all_df["rubric_id"].astype(str)
    all_df["item_id"] = all_df["item_id"].astype(str)

    all_df = all_df[all_df[JUDGE_COL].isin(JUDGES)]

    results: List[Dict[str, Any]] = []
    grouped = all_df.groupby(["question_id", "rubric_id"], dropna=False)
    total_groups = len(grouped)

    for idx, ((question_id, rubric_id), panel_df) in enumerate(grouped, start=1):
        question_rows = dataset_df[dataset_df["id"] == question_id]
        if question_rows.empty:
            continue
        qrow = question_rows.iloc[0]

        judge_item_scores = build_item_scores(panel_df)
        available_judges = sorted(judge_item_scores.keys())
        pairwise = []

        for i in range(len(available_judges)):
            for j in range(i + 1, len(available_judges)):
                ja, jb = available_judges[i], available_judges[j]
                ar = pairwise_agreement(
                    judge_item_scores.get(ja, {}),
                    judge_item_scores.get(jb, {}),
                    rubric_id,
                )
                pairwise.append({"judge_a": ja, "judge_b": jb, "agreement": ar})

        pairwise_vals = [x["agreement"] for x in pairwise]
        panel_class = classify_panel(pairwise_vals, threshold=0.8)

        result = {
            "question_id": int(question_id) if not pd.isna(question_id) else None,
            "domain": qrow.get("domain"),
            "source_dataset": qrow.get("source_dataset"),
            "question": qrow.get("question"),
            "reference_answer": qrow.get("answer"),
            "rubric_id": rubric_id,
            "judges_available": available_judges,
            "n_judges": len(available_judges),
            "pairwise_agreement": pairwise,
            "panel_agreement_class": panel_class,
            "judge_item_scores": judge_item_scores,
        }
        results.append(result)

        if idx % 500 == 0 or idx == total_groups:
            print(f"  [{idx}/{total_groups}] processed")

    summary = Counter(r["panel_agreement_class"] for r in results)

    output = {
        "metadata": {
            "dataset_path": str(DATASET_PATH),
            "combined_csv_path": str(COMBINED_CSV),
            "n_results": len(results),
            "judges": JUDGES,
            "agreement_threshold": 0.8,
            "note": "Computed from combined four-judge CSV. No live LLM calls.",
        },
        "summary": dict(summary),
        "results": results,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nSaved -> {OUTPUT_PATH}")
    print(f"Total (question, rubric) pairs: {len(results)}")
    print("Agreement class distribution:")
    for k, v in sorted(summary.items()):
        print(f"  {k:16s}: {v:5d}  ({100*v/len(results):.1f}%)")


if __name__ == "__main__":
    main()
