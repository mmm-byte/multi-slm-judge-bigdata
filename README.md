# Multi-SLM Medical Judge

A privacy-preserving framework for evaluating AI-generated medical answers using a panel of four locally deployed small language models (SLMs). The panel runs entirely on local hardware — no data leaves the device — making it suitable for HIPAA-constrained clinical settings.

The framework computes a normalized pairwise agreement score across all judges and reports a quality score only when sufficient consensus is reached. Low-agreement cases are routed to human review rather than silently accepted.

## What This Repo Contains

- **96,000 item-level scores** from 4 judges × 5 rubrics × 1,000 questions
- **5 experiments** covering rubric comparison, scale sensitivity, judge ablation, data-driven thresholds, and inter-LLM deliberation
- **All Python scripts** — no GPU or LLM calls needed to reproduce any result
- **7 publication-ready figures**
- **5 rubric definitions** in JSON format

## Key Findings

| Finding | Value |
|---|---|
| Total item-level scores | 96,000 |
| Mean pairwise agreement across all rubrics | 67.5% |
| Rubric with highest agreement | PEMAT (Binary, 75.9%) |
| Rubric with lowest agreement | HealthBench (Binary, 52.9%) |
| Scale effect (PEMAT binary vs Likert) | 2.6 pp drop |
| Inter-LLM Deliberation improvement | +24.9 pp (63.7% → 88.7%) |
| Fully-agreed panels after deliberation | 4.77× increase |

**Removing BioMistral increases agreement by 8.1 pp** — it is the most conservative scorer and the primary source of disagreement. Removing MedAlpaca decreases agreement by 4.8 pp — it shares architecture with Meditron and drives the highest same-architecture agreement.

**Meditron and MedAlpaca agree most** (77.7%, both LLaMA-2). BioMistral and MedGemma agree least (57.1%, cross-architecture). Architectural diversity is a source of disagreement — and therefore a source of evaluation robustness.

## The Four Judges

| Judge | Architecture | Parameters | Item-Leading Rate |
|---|---|---|---|
| MedGemma-4B-IT | Gemma-3 | 4B | 67.9% |
| BioMistral-7B | Mistral | 7B | 40.7% |
| Meditron-7B | LLaMA-2 | 7B | 70.9% |
| MedAlpaca-7B | LLaMA-2 | 7B | 79.0% |

Item-leading rate = fraction of items where the judge gives the highest (or tied-for-highest) score. A very high leading rate may inflate agreement statistics.

## The Five Rubrics

| Rubric | Scale | Criteria |
|---|---|---|
| PEMAT (R1) | Binary | Plain language, organization, focus, actionable steps, barriers |
| HealthBench (R2) | Binary | Correctness, safety, escalation, uncertainty, referral |
| ClinicalEval (R3) | Likert 1–5 | Accuracy, safety, relevance, completeness, clarity |
| Prometheus (R4) | Likert 1–5 | Instruction-following, factuality, coherence, completeness |
| PEMAT-Likert (R5) | Likert 1–5 | Same criteria as R1 (controlled pair) |

The R1/R5 pair uses identical criteria with different scales, isolating the pure effect of scale choice.

## Repository Structure

```
├── README.md                          ← You are here
├── paper/
│   └── bigdata2026_paper.tex          ← LaTeX source
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
https://github.com/mmm-byte/multi-slm-judge-bigdata/releases/download/v1.0/all_four_judges_item_scores_bigdata_valid_only.csv
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

## The Agreement Metric

The framework uses a normalized pairwise agreement score:

```
Agr = (2 / N(N-1)) × Σ_{i<j} [ 1 - (1/|R|) × Σ_k (|s_i^k - s_j^k| / max_k) ]
```

Where `N` is the number of judges, `|R|` is the number of rubric items, `s_i^k` is the score from judge `i` on item `k`, and `max_k` is the maximum score for item `k`. The normalization by `max_k` makes binary and Likert scores directly comparable. `Agr ∈ [0,1]`, where 1.0 = perfect consensus.

Based on `Agr`, each case is routed to one of four levels:
- **Full Agreement** (Agr ≥ θ_FA): Report quality score, high confidence
- **Majority Agreement** (θ_MA ≤ Agr < θ_FA): Report with confidence note
- **Split** (θ_SP ≤ Agr < θ_MA): Route to human review
- **Disagreement** (Agr < θ_SP): Escalate to expert

Default thresholds: θ_FA=0.95, θ_MA=0.75, θ_SP=0.50. Data-driven calibration using empirical percentiles is recommended.

## The Five Experiments

### Exp1: Rubric Comparison at Scale
Per-rubric agreement analysis across 1,000 questions. Binary rubrics outperform Likert by a small margin on the controlled PEMAT pair (75.9% vs 73.3%, a 2.6 pp gap), with a much larger shift in the agreement class distribution. HealthBench shows the most disagreement across all domains.

### Exp2: Scoring Scale Sensitivity
Controlled comparison of PEMAT binary vs PEMAT-Likert. Identical criteria, different scales. The agreement class distribution shifts dramatically even when mean agreement is similar — full-agreement cases drop from 348 to 196 while split cases rise from 172 to 424.

### Exp3: Per-Judge Ablation
Removing each judge and recomputing agreement. Reveals a tension between agreement and architectural diversity: removing BioMistral increases agreement by 8.1 pp but eliminates the only Mistral-architecture voice.

### Exp4: Data-Driven Threshold Calibration
Empirical percentiles of 30,000 pairwise agreement values show mean 67.5%, std 27.7%, quartiles at 48.0% / 76.0% / 90.0%. Recommends calibrating thresholds from historical data rather than adopting defaults.

### Exp5: Inter-LLM Deliberation
One round of structured peer feedback. Each judge that scored differently from the peer median on an item is shown the other judges' scores and rationales, then its score moves toward the peer median by 50% of the gap (75% if it was the unique outlier). Mean agreement improves from 63.7% to 88.7% (+24.9 pp). Fully-agreed panels increase 4.77×.

## How the Framework Works

### Scoring
1. Each judge independently receives a question, answer, and rubric
2. The judge scores every item in the rubric
3. The framework computes pairwise agreement between all judge pairs
4. If agreement exceeds θ_MA, a quality score is reported
5. Otherwise, the case is routed to human review

### Inter-LLM Deliberation
1. After initial scoring, identify items where a judge disagreed with the peer median
2. Show the flagged judge its peers' scores and rationales for those items
3. Move the judge's score toward the peer median by 50% of the gap (75% if it was the unique outlier)
4. Recompute agreement class

## Data Repairs

Three scores (0.003% of 96,000) were recovered from raw model outputs where the parser failed but the model's intent was unambiguous. 88 binary values (0.09%) were repaired via nearest-neighbor rounding. All repairs are documented in `data/repair_log.md`.

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

## Limitations

1. **No physician validation** — high agreement ≠ clinical correctness
2. **Short answers only** — median 29 words, max 209 words
3. **Five domains** — rare specialties (psychiatry, oncology) untested
4. **Deliberation is simulated** — live re-prompting needed for confirmation
5. **MedAlpaca rationales are mostly non-substantive** — 22,995 of 24,000 rows have placeholder rationale like `(primed-first-line)` or `(extracted)`
6. **14,835 blank rationales** across all judges

## Environment

- **Python**: 3.10+
- **Dependencies**: pandas, numpy, plotly, kaleido
- **No GPU required** — all experiments run on CPU
- **No LLM calls** — all results computed from pre-existing scores

## License

MIT License. All benchmark datasets are used under their respective open licenses. Model checkpoints are not redistributed and must be obtained directly from their original sources.
