#!/usr/bin/env python3
"""Experiment 4: Agreement Visualizations (from Exp2 results JSON).

Generates publication-ready figures from Exp2 agreement results:
  - Box plot: mean pairwise agreement per rubric
  - Stacked bar: agreement class distribution per rubric
  - Box plot: mean pairwise agreement per domain
  - Stacked bar: agreement class distribution per domain

No LLM calls — reads Exp2 JSON output.

Usage:
    python bigdata_1000/experiments/exp4_boxplot_from_csv.py

Output:
    bigdata_1000/figures/fig_exp4_agreement_by_rubric.png
    bigdata_1000/figures/fig_exp4_class_by_rubric.png
    bigdata_1000/figures/fig_exp4_agreement_by_domain.png
    bigdata_1000/figures/fig_exp4_class_by_domain.png
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Dict, List

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

BIGDATA_DIR = Path(__file__).resolve().parent.parent
EXP2_PATH = BIGDATA_DIR / "results" / "exp2_agreement_results.json"
OUTPUT_DIR = BIGDATA_DIR / "figures"

RUBRIC_LABELS = {
    "rubric1_pemat": "PEMAT",
    "rubric2_healthbench": "HealthBench",
    "rubric3_clinical_eval": "Clinical Eval",
    "rubric4_prometheus": "Prometheus",
    "rubric5_pemat_likert": "PEMAT-Likert",
}

AGREEMENT_ORDER = ["full_disagree", "split", "majority_agree", "fully_agree"]
CLASS_COLORS = {
    "full_disagree": "#d62728",
    "split": "#ff7f0e",
    "majority_agree": "#2ca02c",
    "fully_agree": "#1f77b4",
}


def load_exp2_dataframe():
    with open(EXP2_PATH) as f:
        data = json.load(f)

    results = data.get("results", data if isinstance(data, list) else [])

    rows = []
    for r in results:
        rubric_id = r.get("rubric_id")
        domain = r.get("domain")
        agreement_class = r.get("panel_agreement_class")
        pairwise = r.get("pairwise_agreement", [])

        mean_pw = None
        vals = [p.get("agreement") if isinstance(p, dict) else p for p in pairwise]
        vals = [v for v in vals if v is not None]
        if vals:
            mean_pw = sum(vals) / len(vals) * 100

        if agreement_class is None or rubric_id is None:
            continue

        rows.append({
            "rubric_id": rubric_id,
            "rubric_label": RUBRIC_LABELS.get(rubric_id, rubric_id),
            "domain": domain,
            "agreement_class": agreement_class,
            "mean_pairwise_pct": mean_pw,
        })

    return pd.DataFrame(rows)


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if not EXP2_PATH.exists():
        print(f"ERROR: {EXP2_PATH} not found. Run exp2_agreement_from_csv.py first.")
        return

    df = load_exp2_dataframe()
    print(f"Loaded {len(df)} question-rubric results from Exp2")

    df_valid = df.dropna(subset=["mean_pairwise_pct"])

    # ── Figure 1: Box plot by rubric ──────────────────────────────────────
    fig1 = px.box(
        df_valid,
        x="rubric_label",
        y="mean_pairwise_pct",
        color="rubric_label",
        points="outliers",
        title="Mean Pairwise Agreement by Rubric (1000 Questions, 4 Judges)",
    )
    fig1.update_layout(showlegend=False, yaxis_title="Mean Pairwise Agreement (%)")
    fig1.write_image(OUTPUT_DIR / "fig_exp4_agreement_by_rubric.png", width=1200, height=600)
    print("  Saved fig_exp4_agreement_by_rubric.png")

    # ── Figure 2: Stacked bar — agreement class by rubric ─────────────────
    class_counts = df.groupby(["rubric_label", "agreement_class"]).size().unstack(fill_value=0)
    for col in AGREEMENT_ORDER:
        if col not in class_counts.columns:
            class_counts[col] = 0
    class_counts = class_counts[AGREEMENT_ORDER]
    class_pct = class_counts.div(class_counts.sum(axis=1), axis=0) * 100

    fig2 = go.Figure()
    for cls in AGREEMENT_ORDER:
        fig2.add_trace(go.Bar(
            name=cls.replace("_", " ").title(),
            x=class_pct.index,
            y=class_pct[cls],
            marker_color=CLASS_COLORS[cls],
        ))
    fig2.update_layout(
        barmode="stack",
        title="Agreement Class Distribution by Rubric (1000 Questions)",
        yaxis_title="% of (question, rubric) pairs",
    )
    fig2.write_image(OUTPUT_DIR / "fig_exp4_class_by_rubric.png", width=1200, height=600)
    print("  Saved fig_exp4_class_by_rubric.png")

    # ── Figure 3: Box plot by domain ──────────────────────────────────────
    fig3 = px.box(
        df_valid,
        x="domain",
        y="mean_pairwise_pct",
        color="domain",
        points="outliers",
        title="Mean Pairwise Agreement by Clinical Domain (1000 Questions, All Rubrics)",
    )
    fig3.update_layout(showlegend=False, yaxis_title="Mean Pairwise Agreement (%)")
    fig3.write_image(OUTPUT_DIR / "fig_exp4_agreement_by_domain.png", width=1200, height=600)
    print("  Saved fig_exp4_agreement_by_domain.png")

    # ── Figure 4: Stacked bar — agreement class by domain ─────────────────
    domain_counts = df.groupby(["domain", "agreement_class"]).size().unstack(fill_value=0)
    for col in AGREEMENT_ORDER:
        if col not in domain_counts.columns:
            domain_counts[col] = 0
    domain_counts = domain_counts[AGREEMENT_ORDER]
    domain_pct = domain_counts.div(domain_counts.sum(axis=1), axis=0) * 100

    fig4 = go.Figure()
    for cls in AGREEMENT_ORDER:
        fig4.add_trace(go.Bar(
            name=cls.replace("_", " ").title(),
            x=domain_pct.index,
            y=domain_pct[cls],
            marker_color=CLASS_COLORS[cls],
        ))
    fig4.update_layout(
        barmode="stack",
        title="Agreement Class Distribution by Clinical Domain (1000 Questions, All Rubrics)",
        yaxis_title="% of (question, rubric) pairs",
    )
    fig4.write_image(OUTPUT_DIR / "fig_exp4_class_by_domain.png", width=1200, height=600)
    print("  Saved fig_exp4_class_by_domain.png")

    print(f"\nAll figures saved to {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
