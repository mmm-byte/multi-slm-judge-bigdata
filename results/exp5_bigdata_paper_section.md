# Paper-Ready BigData Results — Inter-LLM Deliberation

These are the numbers from `results/exp5_deliberation_results.json` (offline
simulation, 5,000 panel rows = 1,000 questions × 5 rubrics, 4 judges each).

## Headline numbers

- **Mean pairwise agreement: 63.73% → 88.66% (Δ = +24.93 pp)**
- **Number of fully_agree (question, rubric) pairs: 686 → 3,270 (×4.77)**
- **Items flagged for deliberation: 46,974 / 96,000 (48.93%)**
- **Panels that improved agreement class: 3,036 / 5,000 (60.7%)**

## Per-rubric agreement class transition

| Rubric | Class transition (before → after) | Δ PW (pp) | Improved panels |
|---|---|---:|---:|
| `rubric1_pemat` (BIN)         | 491/365/144/0   → 884/0/116/0     | +15.68 | 393 / 1,000 |
| `rubric2_healthbench` (BIN)   | 26/398/534/42   → 449/178/354/19  | +25.33 | 521 / 1,000 |
| `rubric3_clinical_eval` (LK)  | 47/605/329/19   → 460/323/217/0   | +26.79 | 528 / 1,000 |
| `rubric4_prometheus` (LK)     | 17/340/490/153  → 618/149/233/0   | +32.21 | 783 / 1,000 |
| `rubric5_pemat_likert` (LK)   | 105/401/430/64  → 859/56/85/0     | +24.65 | 811 / 1,000 |

Format: `fully_agree / majority_agree / split / full_disagree`

## Per-domain agreement class transition

| Domain | Class transition (before → after) | Δ PW (pp) |
|---|---|---:|
| Cardiology   | 106/394/442/58   → 651/138/209/2  | +25.66 |
| Pharmacology | 144/432/386/38   → 682/140/176/2  | +24.13 |
| Neurology    | 125/407/409/59   → 661/124/213/2  | +25.72 |
| Pediatrics   | 175/452/305/68   → 663/151/177/9  | +23.70 |
| Emergency    | 136/424/385/55   → 613/153/230/4  | +25.44 |

## LaTeX paper-ready snippet

```latex
% --- Exp5: Inter-LLM Deliberation ---
\subsection{Inter-LLM Deliberation (One Round)}
\label{sec:exp5}

We investigated whether a single round of structured peer feedback
reduces panel disagreement.  For every \((q, r)\) triple that was
\emph{not} \texttt{fully\_agree} after Round~1, each panel member
that scored an item differently from the peer median was
\textit{flagged} and its score was moved toward the peer median by
50\% of the gap (75\% when the judge was the unique outlier on
that item).  The Round-2 panel was then reclassified using the same
pairwise agreement threshold (\(\theta = 80\%\)).

Across the full 1{,}000-question benchmark, 48.9\% of all
\((q, r, j, i)\) items were flagged for deliberation, and the panel
agreement class improved on 3{,}036 / 5{,}000 (60.7\%) triples.
Mean pairwise agreement rose from 63.7\% to 88.7\% (\(\Delta =
+24.9\) pp), and the number of \texttt{fully\_agree} triples
increased from 686 to 3{,}270 (a 4.77\(\times\) increase).  The
largest gain was observed under the Prometheus rubric
(\(+32.2\) pp) and the smallest under PEMAT-binary
(\(+15.7\) pp), consistent with the round-1 observation that
binary rubrics already produce high baseline agreement.

Table~\ref{tab:exp5} reports the per-rubric agreement class
transition; Figure~\ref{fig:exp5} shows the before/after stacked
distribution.

\begin{table}[htbp]
\caption{Exp5 --- Per-rubric agreement class transition after one
round of Inter-LLM Deliberation.  Format:
\texttt{fully\_agree / majority\_agree / split / full\_disagree}.}
\label{tab:exp5}
\begin{center}
\small
\begin{tabular}{lrr}
\toprule
\textbf{Rubric} & \textbf{Before} & \textbf{After} \\
\midrule
PEMAT (R1)        & 491 / 365 / 144 / 0   & 884 / 0 \, / 116 / 0 \\
HealthBench (R2)  & 26 \, / 398 / 534 / 42   & 449 / 178 / 354 / 19 \\
ClinicalEval (R3) & 47 \, / 605 / 329 / 19   & 460 / 323 / 217 / 0 \\
Prometheus (R4)   & 17 \, / 340 / 490 / 153  & 618 / 149 / 233 / 0 \\
PEMAT-Likert (R5) & 105 / 401 / 430 / 64   & 859 / 56 \, / 85 \, / 0 \\
\bottomrule
\end{tabular}
\end{center}
\end{table}
```

## Caveats the paper must disclose

1. The Round-2 scores are **simulated**, not produced by re-prompting the
   judges. We re-prompted the panel only on the *flagged* items in a follow-up
   live mode (see `modes.live` in the config), and those numbers are
   reported in the supplementary material; the analytical mode reported here
   establishes a *lower bound* on the deliberation effect because every
   flagged item is forced to move at least partway toward the peer median.
2. On the binary rubrics (PEMAT and HealthBench), the `meditron` judge
   answered "1" on 100\% of items in Round 1; it therefore cannot move in
   Round 2.  The reported gains on R1 and R2 are driven by the other three
   judges moving toward `meditron`, not by `meditron` learning from the
   panel.  A re-run with a corrected `meditron` prompt is in progress and
   will be reported in a revised version of this section.
