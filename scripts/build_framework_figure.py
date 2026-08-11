"""Regenerate framework.png for the IEEE Big Data 2026 paper.

The figure is a single, top-to-bottom flow chart matching the visual
style of the original framework figure. The only addition is the
EXP5 Inter-LLM Deliberation feedback path: it lives on the right side
and returns from the side back to the judge row, never back up the
middle of the chart.
"""
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

# ---- canvas ----------------------------------------------------------------
fig, ax = plt.subplots(figsize=(9, 10.5))
ax.set_xlim(0, 90)
ax.set_ylim(0, 110)
ax.set_aspect("equal")
ax.axis("off")

# color palette (soft, paper-friendly)
COL_INPUT   = "#DCEAFE"
COL_JUDGE   = "#FFF1C2"
COL_AGR     = "#D5F1D8"
COL_DECIDE  = "#E3E1F9"
COL_DELIB   = "#FBDCE8"
COL_OUT_FA  = "#B7E5C2"
COL_OUT_MA  = "#FCE5A0"
COL_OUT_SP  = "#F4B5B5"
COL_OUT_DD  = "#7F1D1D"

EDGE         = "#1F2937"
DELIB_EDGE   = "#9D174D"

# ---- helpers --------------------------------------------------------------
def box(cx, cy, w, h, text, fc, ec=EDGE, fontsize=9, weight="bold",
        textcolor="#0F172A"):
    p = FancyBboxPatch(
        (cx - w / 2, cy - h / 2), w, h,
        boxstyle="round,pad=0.3,rounding_size=0.8",
        linewidth=1.3, facecolor=fc, edgecolor=ec,
    )
    ax.add_patch(p)
    ax.text(cx, cy, text, ha="center", va="center",
            fontsize=fontsize, fontweight=weight, color=textcolor)

def arrow(x1, y1, x2, y2, color=EDGE, curve=0.0, lw=1.3, style="-|>",
          label=None, label_pos=0.5, label_color=None, label_fs=8):
    arr = FancyArrowPatch(
        (x1, y1), (x2, y2),
        arrowstyle=style, mutation_scale=14,
        color=color, linewidth=lw,
        connectionstyle=f"arc3,rad={curve}",
    )
    ax.add_patch(arr)
    if label is not None:
        lx = x1 + (x2 - x1) * label_pos + curve * 6
        ly = y1 + (y2 - y1) * label_pos + curve * 6
        ax.text(lx, ly, label, fontsize=label_fs,
                color=label_color or color, fontweight="bold",
                ha="center", va="center",
                bbox=dict(boxstyle="round,pad=0.18",
                          fc="white", ec="none", alpha=0.9))

# ---- title ----------------------------------------------------------------
ax.text(45, 107,
        "Multi-SLMs-as-Judge with Inter-LLM Deliberation",
        ha="center", va="center", fontsize=14, fontweight="bold")
ax.text(45, 104.2,
        "Top-down flow: judge panel  ->  agreement  ->  threshold routing  "
        "->  reporting (or deliberation re-prompt  ->  routing again)",
        ha="center", va="center", fontsize=9, color="#475569", style="italic")

# ---- row 1: inputs (three small boxes in a row) --------------------------
box(18, 97, 22, 5.5, "Question $q$",  COL_INPUT, fontsize=10)
box(45, 97, 22, 5.5, "Answer $a$",    COL_INPUT, fontsize=10)
box(72, 97, 22, 5.5, "Rubric $R$",    COL_INPUT, fontsize=10)

# ---- row 2: judge panel (4 boxes in a row) -------------------------------
judge_y = 85
judge_xs = [13, 31, 49, 67]
for i, x in enumerate(judge_xs):
    box(x, judge_y, 14, 6, f"$J_{i+1}$  (SLM)", COL_JUDGE, fontsize=10)

# ---- row 3: pairwise agreement ------------------------------------------
box(40, 71, 36, 6.5, "Pairwise Agreement Score $\\mathrm{Agr}$  (Eq.\\,1)",
    COL_AGR, fontsize=10.5)

# ---- row 4: threshold decision -----------------------------------------
box(40, 57, 38, 6.5,
    "Compare $\\mathrm{Agr}$ to thresholds  $\\theta_{FA},\\theta_{MA},\\theta_{SP}$",
    COL_DECIDE, fontsize=9.5)

# ---- row 5: outcomes (4 stacked in the main column) --------------------
# FA
box(40, 44, 36, 5.5, "Full Agreement (FA)  ->  report $\\hat{S}$",
    COL_OUT_FA, fontsize=9.5)
# MA
box(40, 36, 36, 5.5, "Majority Agreement (MA)  ->  report $\\hat{S}$ w/ note",
    COL_OUT_MA, fontsize=9.5)
# SP  (routed into the deliberation feedback on the right)
box(40, 27.5, 36, 5.5, "Split (SP)  ->  enter Inter-LLM Deliberation",
    COL_OUT_SP, fontsize=9.5)
# D
box(40, 19, 36, 5.5, "Disagreement (D)  ->  human review",
    COL_OUT_DD, fontsize=9.5, textcolor="white")

# ---- right-side deliberation feedback (returns from the side) ----------
# Deliberation module on the right
box(73, 27.5, 28, 8,
    "Inter-LLM Deliberation\n(EXP5): re-prompt disagreeing\n"
    "judges with peer scores & rationales",
    COL_DELIB, ec=DELIB_EDGE, fontsize=8.5)

# Feedback path: from the right side of the SP box, around the right,
# up to the right side of the judge row.
arrow(58, 27.5, 73 - 14, 27.5, color=DELIB_EDGE, lw=1.4,
      label="SP cases\nre-prompted", label_pos=0.65,
      label_color=DELIB_EDGE, label_fs=8)
arrow(73, 31.5, 73, 78, curve=0.0, color=DELIB_EDGE, lw=1.4, style="-")
arrow(73, 78, 67 + 7, 85, color=DELIB_EDGE, lw=1.4,
      label="Revised scores\nre-enter Agr", label_pos=0.55,
      label_color=DELIB_EDGE, label_fs=8)

# "Disagreement -> human review" arrow leaving the D box
arrow(58, 19, 84, 19, color=COL_OUT_DD, lw=1.4,
      label="escalate", label_pos=0.5,
      label_color=COL_OUT_DD, label_fs=8)

# ---- main column arrows (top -> bottom) --------------------------------
# inputs -> judges
for x in judge_xs:
    arrow(45, 97 - 2.75, x, judge_y + 3, color=EDGE, lw=1.1)
# judges -> pairwise
for x in judge_xs:
    arrow(x, judge_y - 3, 40, 71 + 3.25, color=EDGE, lw=1.1)
# pairwise -> threshold
arrow(40, 71 - 3.25, 40, 57 + 3.25, color=EDGE, lw=1.2)
# threshold -> outcomes (FA, MA, SP, D)
arrow(40, 57 - 3.25, 40, 44 + 2.75, color=EDGE, lw=1.2)
arrow(40, 44 - 2.75, 40, 36 + 2.75, color=EDGE, lw=1.2)
arrow(40, 36 - 2.75, 40, 27.5 + 2.75, color=EDGE, lw=1.2)
arrow(40, 27.5 - 2.75, 40, 19 + 2.75, color=EDGE, lw=1.2)

# small legend in the lower-left corner
ax.text(7, 6, "FA = Full Agreement    MA = Majority Agreement    "
        "SP = Split    D = Disagreement",
        ha="left", va="center", fontsize=8, color="#475569")
ax.text(7, 3, "Colored arrows (right) = EXP5 deliberation feedback path.",
        ha="left", va="center", fontsize=8, color=DELIB_EDGE, fontweight="bold")

plt.tight_layout()
out = "/Users/mahindragupthakotha/Git Repo/multi-slm-judge-bigdata/paper/framework.png"
plt.savefig(out, dpi=220, bbox_inches="tight", facecolor="white")
print("wrote", out)
