# Data Repair Log — 1000-Question Combined CSV

This documents every repair applied to the 96,000-row combined four-judge CSV.

## Source CSVs

| Judge | Source CSV | Rows | Status |
|---|---|---|---|
| BioMistral | `biomistral/biomistral_item_scores.csv` | 24,000 | No repairs needed |
| MedGemma | `medgemma/medgemma_item_scores.csv` | 24,000 | 2 scores recovered (see below) |
| Meditron | `meditron_eval_outputs/judge_outputs/meditron/meditron_item_scores.csv` | 24,000 | No repairs needed |
| MedAlpaca | `MedAlpaca_Judge_Project/medalpaca/medalpaca_item_scores_validated_v5_complete.csv` | 24,000 | Rebuilt from raw; 1 score recovered (see below) |

## MedAlpaca — Rebuilt from Raw

The original validated CSV (`medalpaca_item_scores_validated_v4-2.csv`) had only 21,333 rows.
Questions 876–1000 were mostly missing — the validation script was interrupted.

**Fix:** A new validated CSV (`v5_complete`) was built from the raw 24,000-row source
(`medalpaca_item_scores.csv`). The raw data was complete — all 24,000 rows had valid scores.

## Repaired Binary Values: 88 rows

88 rows had non-0/1 values on BINARY rubrics. These were repaired using
nearest-neighbor rounding (≥0.5 → 1, <0.5 → 0). All are marked
`score_repair_status = repaired_binary_nearest` in the CSV.

These occur when the model outputs a non-binary value (e.g., "0.5", "yes")
on a binary rubric. The repair is deterministic and documented.

## Recovered Scores: 3 rows

### 1. MedGemma Q682, rubric5_pemat_likert, item A1
- **Raw score:** `NA` (model produced out-of-range value)
- **Evidence:** `raw_stage1` shows `A1: 0` — model scored 0 on a 1-5 Likert scale
- **Recovered score:** `1` (clamped to scale minimum)
- **Rationale:** Model output "0" interpreted as lowest possible on 1-5 scale

### 2. MedGemma Q711, rubric5_pemat_likert, item A1
- **Raw score:** `NA` (model produced out-of-range value)
- **Evidence:** `raw_stage1` shows `A1: 0` — model scored 0 on a 1-5 Likert scale
- **Recovered score:** `1` (clamped to scale minimum)
- **Rationale:** Same pattern as Q682

### 3. MedAlpaca Q320, rubric2_healthbench, item HB1
- **Raw score:** `NA` (model didn't produce a parseable score)
- **Evidence:** `raw_stage3_json` shows `{"HB1": "100%"}` — clearly positive binary
- **Recovered score:** `1` (binary positive)
- **Rationale:** Model output "100%" interpreted as binary 1

## Blank Rationales: 14,835 rows

These are rows where the model produced a valid score but no substantive rationale.
Common reasons:
- MedAlpaca: `(primed-first-line)` or `(extracted)` — 22,995 rows
- Meditron: `(primed-first-line)` — model only produced scores, no reasoning
- Other judges: empty or placeholder rationales

## What Was NOT Repaired

- No scores were invented — all repairs are traceable to raw model outputs
- No rationales were fabricated
- No rows were removed to hide problems
- The 3 recovered scores are explicitly marked in the source CSVs
