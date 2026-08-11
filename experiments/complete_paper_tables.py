#!/usr/bin/env python3
"""Complete paper-ready results: scale sensitivity, quality scores, item-leading rates.

Computes three missing pieces from the 96,000-row combined CSV:
  1. Full scale sensitivity — 5 rubrics × 3 scales (BINARY, LIKERT 1-5, 0-10)
  2. Quality score Ŝ per rubric (mean ± std)
  3. Item-leading rates per judge

All computed analytically — no LLM calls needed.

Usage:
    python bigdata_1000/experiments/complete_paper_tables.py

Output:
    bigdata_1000/results/scale_sensitivity_table.csv
    bigdata_1000/results/quality_scores_table.csv
    bigdata_1000/results/item_leading_rates.csv
"""
from __future__ import annotations

import csv, json
from collections import defaultdict, Counter
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd
import numpy as np

BIGDATA_DIR = Path(__file__).resolve().parent.parent
COMBINED_CSV = Path(
    "/Users/mahindragupthakotha/Downloads/judge_outputs/"
    "bigdata_four_model_review/all_four_judges_item_scores_bigdata_valid_only.csv"
)

JUDGES = ["biomistral", "medgemma", "meditron", "medalpaca"]
RUBRICS = [
    "rubric1_pemat",
    "rubric2_healthbench",
    "rubric3_clinical_eval",
    "rubric4_prometheus",
    "rubric5_pemat_likert",
]
RUBRIC_LABELS = {
    "rubric1_pemat": "PEMAT",
    "rubric2_healthbench": "HealthBench",
    "rubric3_clinical_eval": "ClinicalEval",
    "rubric4_prometheus": "Prometheus",
    "rubric5_pemat_likert": "PEMAT-Likert",
}
RUBRIC_SCALES = {
    "rubric1_pemat": "BINARY",
    "rubric2_healthbench": "BINARY",
    "rubric3_clinical_eval": "LIKERT",
    "rubric4_prometheus": "LIKERT",
    "rubric5_pemat_likert": "LIKERT",
}
RUBRIC_MAX_K = {
    "rubric1_pemat": 1,
    "rubric2_healthbench": 1,
    "rubric3_clinical_eval": 5,
    "rubric4_prometheus": 5,
    "rubric5_pemat_likert": 5,
}
RUBRIC_N_ITEMS = {
    "rubric1_pemat": 5,
    "rubric2_healthbench": 5,
    "rubric3_clinical_eval": 5,
    "rubric4_prometheus": 4,
    "rubric5_pemat_likert": 5,
}

AGREEMENT_THRESHOLD = 0.8


def parse_score(x) -> float | None:
    if pd.isna(x):
        return None
    s = str(x).strip().upper()
    if s in {"NA", "N/A", "NONE", ""}:
        return None
    try:
        return float(s)
    except Exception:
        return None


def map_to_scale(score: float, from_lo: float, from_hi: float, to_lo: float, to_hi: float) -> float:
    """Linearly map score from [from_lo, from_hi] to [to_lo, to_hi]."""
    if from_hi == from_lo:
        return to_lo
    return to_lo + (score - from_lo) / (from_hi - from_lo) * (to_hi - to_lo)


def simulate_scale(score: float | None, rubric_id: str, target_scale: str) -> float | None:
    """Simulate what a judge would score under a different scale.

    BINARY:   threshold Likert at midpoint (≥3 → 1, <3 → 0)
    LIKERT 1-5: map binary 0→1, 1→5
    0-10:      linear map from original scale
    """
    if score is None:
        return None

    original_scale = RUBRIC_SCALES[rubric_id]
    max_k = RUBRIC_MAX_K[rubric_id]

    if target_scale == "BINARY":
        if original_scale == "BINARY":
            return score  # already binary
        else:
            # Threshold at midpoint: ≥3 → 1, <3 → 0
            return 1.0 if score >= 3.0 else 0.0

    elif target_scale == "LIKERT_1_5":
        if original_scale == "LIKERT":
            return score  # already 1-5
        else:
            # Binary: 0→1, 1→5
            return 5.0 if score >= 0.5 else 1.0

    elif target_scale == "0_10":
        if original_scale == "BINARY":
            return 10.0 if score >= 0.5 else 0.0
        else:
            # Likert 1-5 → 0-10
            return map_to_scale(score, 1.0, 5.0, 0.0, 10.0)

    return score


def pairwise_agreement(scores_a: List[float | None], scores_b: List[float | None], max_k: float) -> float | None:
    """Paper Eq.1: 1 - (1/|R|) * sum_k (|s_i^k - s_j^k| / max_k)."""
    count = 0
    total_diff = 0.0
    for a, b in zip(scores_a, scores_b):
        if a is None or b is None:
            continue
        total_diff += abs(a - b) / max_k
        count += 1
    if count == 0:
        return None
    return 1.0 - total_diff / count


def classify_panel(pairwise_vals: List[float | None], threshold: float = AGREEMENT_THRESHOLD) -> str:
    valid = [x for x in pairwise_vals if x is not None]
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


def compute_quality_score(judge_scores: Dict[str, List[float | None]], max_k: float) -> float | None:
    """Paper Eq.2: Ŝ = (1/N) * Σ_i [ Σ_k (s_i^k / max_k) / |R| ].

    Equal weights (w_k = 1), normalized to [0,1].
    """
    total = 0.0
    n_judges = 0
    for judge, scores in judge_scores.items():
        valid = [s for s in scores if s is not None]
        if not valid:
            continue
        judge_mean = sum(s / max_k for s in valid) / len(valid)
        total += judge_mean
        n_judges += 1
    if n_judges == 0:
        return None
    return total / n_judges


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

def main():
    print("Loading combined CSV...")
    df = pd.read_csv(COMBINED_CSV, low_memory=False)
    df["question_id"] = pd.to_numeric(df["question_id"], errors="coerce")
    df["rubric_id"] = df["rubric_id"].astype(str)
    df["item_id"] = df["item_id"].astype(str)
    df = df[df["judge_name"].isin(JUDGES)]
    print(f"  {len(df)} rows loaded")

    # ═══════════════════════════════════════════════════════════════════════
    # 1. FULL SCALE SENSITIVITY — 5 rubrics × 3 scales
    # ═══════════════════════════════════════════════════════════════════════
    print("\n" + "=" * 70)
    print("1. FULL SCALE SENSITIVITY (5 rubrics × 3 scales)")
    print("=" * 70)

    TARGET_SCALES = [
        ("BINARY", 1.0),
        ("LIKERT_1_5", 5.0),
        ("0_10", 10.0),
    ]

    scale_results = []
    for rubric_id in RUBRICS:
        sub = df[df["rubric_id"] == rubric_id]
        grouped = sub.groupby("question_id")

        for scale_name, scale_max_k in TARGET_SCALES:
            pw_vals_all = []
            class_counts = Counter()

            for qid, panel in grouped:
                # Build per-judge item scores under target scale
                judge_scores: Dict[str, List[float | None]] = {j: [] for j in JUDGES}
                item_order = sorted(panel["item_id"].unique())

                for item_id in item_order:
                    for judge in JUDGES:
                        jrows = panel[(panel["judge_name"] == judge) & (panel["item_id"] == item_id)]
                        if jrows.empty:
                            judge_scores[judge].append(None)
                        else:
                            raw = parse_score(jrows.iloc[0]["score"])
                            simulated = simulate_scale(raw, rubric_id, scale_name)
                            judge_scores[judge].append(simulated)

                # Compute pairwise agreement
                pairwise = []
                for i in range(len(JUDGES)):
                    for j in range(i + 1, len(JUDGES)):
                        ar = pairwise_agreement(
                            judge_scores[JUDGES[i]],
                            judge_scores[JUDGES[j]],
                            scale_max_k,
                        )
                        pairwise.append(ar)

                valid_pw = [x for x in pairwise if x is not None]
                if valid_pw:
                    pw_vals_all.extend(valid_pw)
                panel_class = classify_panel(pairwise)
                class_counts[panel_class] += 1

            mean_pw = np.mean(pw_vals_all) * 100 if pw_vals_all else 0
            std_pw = np.std(pw_vals_all) * 100 if pw_vals_all else 0
            n = sum(class_counts.values())

            scale_results.append({
                "rubric_id": rubric_id,
                "rubric_label": RUBRIC_LABELS[rubric_id],
                "scale": scale_name,
                "n_questions": n,
                "mean_pw_%": round(mean_pw, 1),
                "std_pw_%": round(std_pw, 1),
                "fully_agree": class_counts.get("fully_agree", 0),
                "majority_agree": class_counts.get("majority_agree", 0),
                "split": class_counts.get("split", 0),
                "full_disagree": class_counts.get("full_disagree", 0),
            })

    # Print as a nice table
    scale_df = pd.DataFrame(scale_results)
    print("\nScale Sensitivity Table:")
    print(f"{'Rubric':<16} {'Scale':<12} {'Mean PW%':>10} {'Std%':>8} {'FA':>6} {'MA':>6} {'SP':>6} {'FD':>6}")
    print("-" * 70)
    for _, row in scale_df.iterrows():
        print(f"{row['rubric_label']:<16} {row['scale']:<12} {row['mean_pw_%']:>10.1f} {row['std_pw_%']:>8.1f} "
              f"{row['fully_agree']:>6} {row['majority_agree']:>6} {row['split']:>6} {row['full_disagree']:>6}")

    # Pivot for paper table format
    print("\nPaper-Ready Pivot (Mean PW%):")
    pivot = scale_df.pivot(index="rubric_label", columns="scale", values="mean_pw_%")
    # Bold the max per row
    for idx, row in pivot.iterrows():
        max_val = row.max()
        parts = []
        for col in pivot.columns:
            val = row[col]
            marker = "**" if val == max_val else ""
            parts.append(f"{marker}{val:.1f}{marker}")
        print(f"  {idx:<14} {' & '.join(parts)}")

    # Save
    scale_df.to_csv(BIGDATA_DIR / "results" / "scale_sensitivity_table.csv", index=False)
    print(f"\nSaved -> {BIGDATA_DIR / 'results' / 'scale_sensitivity_table.csv'}")

    # ═══════════════════════════════════════════════════════════════════════
    # 2. QUALITY SCORE Ŝ PER RUBRIC
    # ═══════════════════════════════════════════════════════════════════════
    print("\n" + "=" * 70)
    print("2. QUALITY SCORE Ŝ PER RUBRIC")
    print("=" * 70)

    quality_results = []
    for rubric_id in RUBRICS:
        max_k = RUBRIC_MAX_K[rubric_id]
        sub = df[df["rubric_id"] == rubric_id]
        grouped = sub.groupby("question_id")

        s_hats = []
        for qid, panel in grouped:
            judge_scores: Dict[str, List[float | None]] = {j: [] for j in JUDGES}
            item_order = sorted(panel["item_id"].unique())

            for item_id in item_order:
                for judge in JUDGES:
                    jrows = panel[(panel["judge_name"] == judge) & (panel["item_id"] == item_id)]
                    if jrows.empty:
                        judge_scores[judge].append(None)
                    else:
                        judge_scores[judge].append(parse_score(jrows.iloc[0]["score"]))

            s_hat = compute_quality_score(judge_scores, max_k)
            if s_hat is not None:
                s_hats.append(s_hat)

        mean_s = np.mean(s_hats) if s_hats else 0
        std_s = np.std(s_hats) if s_hats else 0

        quality_results.append({
            "rubric_id": rubric_id,
            "rubric_label": RUBRIC_LABELS[rubric_id],
            "scale": RUBRIC_SCALES[rubric_id],
            "n_questions": len(s_hats),
            "mean_S_hat": round(mean_s, 4),
            "std_S_hat": round(std_s, 4),
        })

    quality_df = pd.DataFrame(quality_results)
    print("\nQuality Scores:")
    for _, row in quality_df.iterrows():
        print(f"  {row['rubric_label']:<16} {row['scale']:<8} Ŝ = {row['mean_S_hat']:.4f} ± {row['std_S_hat']:.4f}")

    quality_df.to_csv(BIGDATA_DIR / "results" / "quality_scores_table.csv", index=False)
    print(f"\nSaved -> {BIGDATA_DIR / 'results' / 'quality_scores_table.csv'}")

    # ═══════════════════════════════════════════════════════════════════════
    # 3. ITEM-LEADING RATES PER JUDGE
    # ═══════════════════════════════════════════════════════════════════════
    print("\n" + "=" * 70)
    print("3. ITEM-LEADING RATES PER JUDGE")
    print("=" * 70)

    # For each (question_id, rubric_id, item_id), find which judge gave the
    # highest score. "Item-leading rate" = fraction of items where this judge
    # is the sole highest scorer (or tied for highest).

    leading_counts = Counter()
    total_items = Counter()
    sole_leading = Counter()

    for rubric_id in RUBRICS:
        sub = df[df["rubric_id"] == rubric_id]
        grouped = sub.groupby(["question_id", "item_id"])

        for (qid, item_id), panel in grouped:
            judge_scores = {}
            for _, row in panel.iterrows():
                s = parse_score(row["score"])
                if s is not None:
                    judge_scores[row["judge_name"]] = s

            if len(judge_scores) < 2:
                continue

            max_score = max(judge_scores.values())
            leaders = [j for j, s in judge_scores.items() if s == max_score]

            for j in leaders:
                leading_counts[j] += 1
                total_items[j] += 1
            if len(leaders) == 1:
                sole_leading[leaders[0]] += 1

    # Also count total items each judge participated in
    for judge in JUDGES:
        total_items[judge] = len(df[df["judge_name"] == judge])

    print("\nItem-Leading Rates:")
    print(f"{'Judge':<14} {'Total Items':>12} {'Led (any)':>10} {'Led %':>8} {'Sole Lead':>10} {'Sole %':>8}")
    print("-" * 65)
    leading_results = []
    for judge in JUDGES:
        total = total_items[judge]
        led = leading_counts.get(judge, 0)
        sole = sole_leading.get(judge, 0)
        led_pct = 100 * led / total if total else 0
        sole_pct = 100 * sole / total if total else 0
        leading_results.append({
            "judge": judge,
            "total_items": total,
            "led_any": led,
            "led_any_pct": round(led_pct, 1),
            "sole_lead": sole,
            "sole_lead_pct": round(sole_pct, 1),
        })
        print(f"  {judge:<14} {total:>12} {led:>10} {led_pct:>7.1f}% {sole:>10} {sole_pct:>7.1f}%")

    leading_df = pd.DataFrame(leading_results)
    leading_df.to_csv(BIGDATA_DIR / "results" / "item_leading_rates.csv", index=False)
    print(f"\nSaved -> {BIGDATA_DIR / 'results' / 'item_leading_rates.csv'}")

    # ═══════════════════════════════════════════════════════════════════════
    # SUMMARY
    # ═══════════════════════════════════════════════════════════════════════
    print("\n" + "=" * 70)
    print("ALL THREE TABLES COMPLETE ✅")
    print("=" * 70)
    print(f"  {BIGDATA_DIR / 'results' / 'scale_sensitivity_table.csv'}")
    print(f"  {BIGDATA_DIR / 'results' / 'quality_scores_table.csv'}")
    print(f"  {BIGDATA_DIR / 'results' / 'item_leading_rates.csv'}")


if __name__ == "__main__":
    main()
