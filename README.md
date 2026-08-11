# Multi-SLM Medical Judge — IEEE Big Data 2026

[![DOI](https://img.shields.io/badge/DOI-10.5281/zenodo.XXXXXXX-blue)](https://doi.org/10.5281/zenodo.XXXXXXX)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

This repository contains the complete code, data, and results for the paper:

> **"Scaling Multi-SLM Medical Evaluation to 1,000 Questions: Agreement, Deliberation, and Panel Diagnostics"**
> *IEEE Big Data 2026*

## Overview

We evaluate whether a panel of four small, locally-deployed medical language models (SLMs, ≤7B parameters) can reliably judge the quality of AI-generated medical answers. The framework runs entirely on local hardware — no data leaves the device — making it suitable for HIPAA-constrained clinical settings.

### Key Results

| Metric | Value |
|---|---|
| Benchmark size | 1,000 questions, 5 clinical domains |
| Total item-level scores | 96,000 (4 judges × 5 rubrics) |
| Mean pairwise agreement | 67.5% (all rubrics) |
| Binary vs Likert gap | 2.6 pp (PEMAT controlled pair) |
| Deliberation improvement | +24.9 pp (63.7% → 88.7%) |
| Fully-agreed panels after deliberation | 4.77× increase |

## Repository Structure

```
├── README.md                          ← You are here
├── paper/
│   └── bigdata2026_paper.tex          ← IEEE Big Data 2026 paper (LaTeX)
├── data/
│   └── repair_log.md                 ← Documents all data repairs
├── experiments/
│   ├── exp2_agreement_from_csv.py     ← Per-rubric agreement analysis
│   ├── exp3_sensitivity_from_csv.py   ← Scale sensitivity (PEMAT binary vs Likert)
│   ├── exp4_boxplot_from_csv.py       ← Agreement visualizations
│   └── complete_paper_tables.py       ← Scale sensitivity, quality scores, item-leading rates
├── results/
│   ├── exp1_dataset_table_bigdata.json    ← Dataset composition
│   ├── exp2_agreement_results.json        ← 5,000 (Q, rubric) agreement results
│   ├── exp3_sensitivity_results.json      ← PEMAT scale comparison
│   ├── exp3_sensitivity_summary.csv       ← Scale effect summary
│   ├── exp5_deliberation_results.json     ← Inter-LLM deliberation
│   ├── exp5_deliberation_summary.csv      ← Deliberation per-rubric
│   ├── scale_sensitivity_table.csv        ← Full scale sensitivity
│   ├── quality_scores_table.csv           ← Quality scores Ŝ
│   └── item_leading_rates.csv            ← Per-judge leading rates
├── figures/
│   ├── fig_exp4_agreement_by_rubric.png
│   ├── fig_exp4_class_by_rubric.png
│   ├── fig_exp4_agreement_by_domain.png
│   ├── fig_exp4_class_by_domain.png
│   ├── fig_exp5_agreement_class_before_after.png
│   ├── fig_exp5_pairwise_delta_by_domain.png
│   └── fig_exp5_pairwise_delta_by_rubric.png
└── rubrics/
    ├── rubric1_pemat.json
    ├── rubric2_healthbench.json
    ├── rubric3_clinical_eval.json
    ├── rubric4_prometheus.json
    └── rubric5_pemat_likert.json
```

## The Combined Dataset

The full 96,000-row combined CSV is available at:
```
https://github.com/<username>/multi-slm-judge-bigdata/releases/download/v1.0/all_four_judges_item_scores_bigdata_valid_only.csv
```

### Dataset Schema

| Column | Description |
|---|---|
| `judge_name` | One of: biomistral, medgemma, meditron, medalpaca |
| `question_id` | 1–1000 |
| `domain` | Cardiology, Pharmacology, Neurology, Pediatrics, Emergency |
| `rubric_id` | rubric1_pemat through rubric5_pemat_likert |
| `item_id` | Rubric-specific item identifier |
| `score` | Raw score (0/1 for binary, 1–5 for Likert) |
| `score_010` | Score normalized to 0–10 scale |
| `rationale` | Judge's reasoning (may be empty or non-substantive) |
| `score_validation_status` | `ok` for all 96,000 rows |
| `score_repair_status` | `not_repaired` or `repaired_binary_nearest` |

## The Four Judges

| Judge | Architecture | Parameters | Item-Leading Rate |
|---|---|---|---|
| MedGemma-4B-IT | Gemma-3 | 4B | 67.9% |
| BioMistral-7B | Mistral | 7B | 40.7% |
| Meditron-7B | LLaMA-2 | 7B | 70.9% |
| MedAlpaca-7B | LLaMA-2 | 7B | 79.0% |

## The Five Rubrics

| Rubric | Scale | Source |
|---|---|---|
| PEMAT (R1) | Binary | Shoemaker et al. 2014 |
| HealthBench (R2) | Binary | Arora et al. 2025 |
| ClinicalEval (R3) | Likert 1–5 | Ho et al. 2024 |
| Prometheus (R4) | Likert 1–5 | Kim et al. 2024 |
| PEMAT-Likert (R5) | Likert 1–5 | Same criteria as R1 |

## Experiments

### Exp1: Rubric Comparison at Scale
Per-rubric agreement analysis across 1,000 questions. Binary rubrics outperform Likert, but the gap is compressed at scale (2.6 pp vs 22 pp on 100 questions).

### Exp2: Scoring Scale Sensitivity
Controlled comparison of PEMAT binary vs PEMAT-Likert. Identical criteria, different scales. The agreement class distribution shifts dramatically even when mean agreement is similar.

### Exp3: Per-Judge Ablation
Removing each judge and recomputing agreement. Removing BioMistral increases agreement by 8.1 pp; removing MedAlpaca decreases it by 4.8 pp. Reveals a tension between agreement and architectural diversity.

### Exp4: Data-Driven Threshold Calibration
Empirical percentiles of 30,000 pairwise agreement values. Recommends calibrating thresholds from historical data rather than adopting defaults.

### Exp5: Inter-LLM Deliberation
One round of structured peer feedback. Mean agreement improves from 63.7% to 88.7% (+24.9 pp). Fully-agreed panels increase 4.77×.

## Reproduction

### Prerequisites
```bash
pip install pandas numpy plotly kaleido
```

### Running the experiments
```bash
# Exp2: Per-rubric agreement
python experiments/exp2_agreement_from_csv.py

# Exp3: Scale sensitivity
python experiments/exp3_sensitivity_from_csv.py

# Exp4: Visualizations (requires Exp2 output)
python experiments/exp4_boxplot_from_csv.py

# Complete paper tables
python experiments/complete_paper_tables.py
```

All experiments read from the combined CSV — no GPU or LLM calls needed.

## Data Repairs

Three scores (0.003% of 96,000) were recovered from raw model outputs where the parser failed but the model's intent was unambiguous. 88 binary values (0.09%) were repaired via nearest-neighbor rounding. All repairs are documented in `data/repair_log.md`.

## Known Limitations

1. **No physician validation** — high agreement ≠ clinical correctness
2. **Short answers only** — median 29 words, max 209 words
3. **Five domains** — rare specialties (psychiatry, oncology) untested
4. **Deliberation is simulated** — live re-prompting needed for confirmation
5. **MedAlpaca rationales are mostly non-substantive** — 22,995 of 24,000 rows
6. **14,835 blank rationales** across all judges

## Citation

```bibtex
@inproceedings{multi-slm-judge-bigdata2026,
  title     = {Scaling Multi-SLM Medical Evaluation to 1,000 Questions:
               Agreement, Deliberation, and Panel Diagnostics},
  author    = {First Author},
  booktitle = {Proceedings of the 2026 IEEE International Conference on Big Data (BigData)},
  year      = {2026}
}
```

## License

MIT License. See LICENSE file for details.

## Related Work

- **EMNLP 2026 Short**: Initial framework proposal (100 questions, HPC)
- **IEEE HealthCom 2026**: Extended experiments with rubric sensitivity (100 questions, HPC)
- **IEEE Big Data 2026** (this paper): Tenfold scale-up with ablation, deliberation, and panel diagnostics (1,000 questions, Colab)
