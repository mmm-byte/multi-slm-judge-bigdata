#!/usr/bin/env python3
"""Experiment 3: Rubric Sensitivity — Scoring Scale Comparison (from combined CSV).

Compares PEMAT binary (rubric1_pemat) vs PEMAT-Likert (rubric5_pemat_likert) —
identical criteria, different scales. Isolates the effect of scale choice
on inter-judge agreement.

No LLM calls — purely analytical from the existing CSV.

Usage:
    python bigdata_1000/experiments/exp3_sensitivity_from_csv.py

Output:
    bigdata_1000/results/exp3_sensitivity_results.json
    bigdata_1000/results/exp3_sensitivity_summary.csv
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
OUTPUT_PATH = BIGDATA_DIR / "results" / "exp3_sensitivity_results.json"
SUMMARY_CSV_PATH = BIGDATA_DIR / "results" / "exp3_sensitivity_summary.csv"

JUDGES = ["biomistral", "medgemma", "meditron", "medalpaca"]
JUDGE_COL = "judge_name"

# Controlled pair: same criteria, different scales
RUBRIC_PAIR = ("rubric1_pemat", "rubric5_pemat_likert")

RUBRIC_MAX_K = {
    "rubric1_pemat": 1,
    "rubric5_pemat_likert": 5,
}


def parse_score(x):
    if pd.isna(x):
        return None
    s = str(x).strip().upper()
    if s in {"NA", "N/A", "NONE", ""}:
        return None
    try:
        return float(s)
    except Exception:
        return None


def pairwise_agreement(scores_a: Dict[str, Any], scores_b: Dict[str, Any], rubric_id: str):
    """Paper Eq.1: 1 - (1/|R|) * sum_k (|s_i^k - s_j^k| / max_k)."""
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


def classify_panel(pairwise_scores: List[Any], threshold: float = 0.8) -> str:
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


def compute_panel_result(panel_df: pd.DataFrame, rubric_id: str) -> Dict[str, Any]:
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
            pairwise.append(ar)
    panel_class = classify_panel(pairwise, threshold=0.8)
    valid_pw = [x for x in pairwise if x is not None]
    mean_pw = sum(valid_pw) / len(valid_pw) if valid_pw else None
    return {
        "n_judges": len(available_judges),
        "pairwise_agreement": pairwise,
        "panel_agreement_class": panel_class,
        "mean_pairwise_agreement": mean_pw,
    }


def main():
    print("=" * 70)
    print("Experiment 3: Rubric Sensitivity — Scale Comparison")
    print(f"Controlled pair: {RUBRIC_PAIR[0]} (BINARY) vs {RUBRIC_PAIR[1]} (LIKERT 1-5)")
    print(f"Combined CSV: {COMBINED_CSV}")
    print("=" * 70)

    dataset_df = pd.read_csv(DATASET_PATH, low_memory=False)
    all_df = pd.read_csv(COMBINED_CSV, low_memory=False)

    all_df["question_id"] = pd.to_numeric(all_df["question_id"], errors="coerce")
    all_df["rubric_id"] = all_df["rubric_id"].astype(str)
    all_df["item_id"] = all_df["item_id"].astype(str)
    all_df = all_df[all_df[JUDGE_COL].isin(JUDGES)]

    results: List[Dict[str, Any]] = []
    rubric_summaries: Dict[str, List[Dict[str, Any]]] = {r: [] for r in RUBRIC_PAIR}

    for rubric_id in RUBRIC_PAIR:
        sub_df = all_df[all_df["rubric_id"] == rubric_id]
        grouped = sub_df.groupby("question_id", dropna=False)

        for question_id, panel_df in grouped:
            question_rows = dataset_df[dataset_df["id"] == question_id]
            if question_rows.empty:
                continue
            qrow = question_rows.iloc[0]

            panel_result = compute_panel_result(panel_df, rubric_id)
            entry = {
                "question_id": int(question_id) if not pd.isna(question_id) else None,
                "domain": qrow.get("domain"),
                "rubric_id": rubric_id,
                **panel_result,
            }
            results.append(entry)
            rubric_summaries[rubric_id].append(entry)

        print(f"  [{rubric_id}] processed {len(rubric_summaries[rubric_id])} questions")

    # Build summary
    summary_rows = []
    for rubric_id, entries in rubric_summaries.items():
        n = len(entries)
        if n == 0:
            continue
        mean_pw_vals = [e["mean_pairwise_agreement"] for e in entries if e["mean_pairwise_agreement"] is not None]
        mean_pw = sum(mean_pw_vals) / len(mean_pw_vals) * 100 if mean_pw_vals else None
        class_counts = Counter(e["panel_agreement_class"] for e in entries)
        summary_rows.append({
            "rubric_id": rubric_id,
            "n": n,
            "mean_pw_%": round(mean_pw, 1) if mean_pw is not None else None,
            "fully_%": round(100 * class_counts.get("fully_agree", 0) / n, 1),
            "majority_%": round(100 * class_counts.get("majority_agree", 0) / n, 1),
            "split_%": round(100 * class_counts.get("split", 0) / n, 1),
            "full_disagree_%": round(100 * class_counts.get("full_disagree", 0) / n, 1),
        })

    summary_df = pd.DataFrame(summary_rows)
    print("\nRubric Sensitivity Summary:")
    print(summary_df.to_string(index=False))

    # Compute the scale effect
    if len(summary_rows) == 2:
        delta = summary_rows[0]["mean_pw_%"] - summary_rows[1]["mean_pw_%"]
        print(f"\n  Scale effect (BINARY - LIKERT): {delta:.1f} pp drop")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(results, f, indent=2)
    summary_df.to_csv(SUMMARY_CSV_PATH, index=False)

    print(f"\nSaved detailed results -> {OUTPUT_PATH}")
    print(f"Saved summary table    -> {SUMMARY_CSV_PATH}")


if __name__ == "__main__":
    main()
