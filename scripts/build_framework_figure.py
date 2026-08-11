"""Regenerate framework.png for the IEEE Big Data 2026 paper.

The figure shows the EXP5 Inter-LLM Deliberation feedback loop:
judges that disagree with the panel after the first round are
re-prompted with the other judges' scores and rationales, so the
framework has a feedback loop rather than a strictly one-shot
routing pipeline.
"""
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

# ---- canvas -----------------------------------------------------------------
fig, ax = plt.subplots(figsize=(11, 6.2))
ax.set_xlim(0, 100)
ax.set_ylim(0, 60)
ax.set_aspect("equal")
ax.axis("off")

# color palette
COL_INPUT   = "#E8F0FE"   # light blue
COL_JUDGE   = "#FEF3C7"   # light amber
COL_AGR     = "#DCFCE7"   # light green
COL_DECIDE  = "#E0E7FF"   # lavender
COL_DELIB   = "#FCE7F3"   # light pink
COL_OUT_FA  = "#BBF7D0"   # green
COL_OUT_MA  = "#FDE68A"   # yellow
COL_OUT_DD  = "#7F1D1D"   # dark red

EDGE = "#1F2937"
DELIB_EDGE = "#9D174D"     # dark pink for the deliberation loop

# ---- helpers ---------------------------------------------------------------
def box(x, y, w, h, text, fc, ec=EDGE, fontsize=9, weight="bold", textcolor="#0F172A"):
    p = FancyBboxPatch(
        (x - w / 2, y - h / 2), w, h,
        boxstyle="round,pad=0.3,rounding_size=0.8",
        linewidth=1.4, facecolor=fc, edgecolor=ec,
    )
    ax.add_patch(p)
    ax.text(x, y, text, ha="center", va="center",
            fontsize=fontsize, fontweight=weight, color=textcolor)

def arrow(x1, y1, x2, y2, label="", color=EDGE, curve=0.0,
          fontsize=8, style="-|>", lw=1.3):
    arr = FancyArrowPatch(
        (x1, y1), (x2, y2),
        arrowstyle=style, mutation_scale=14,
        color=color, linewidth=lw,
        connectionstyle=f"arc3,rad={curve}",
    )
    ax.add_patch(arr)
    if label:
        ax.text((x1 + x2) / 2 + curve * 4, (y1 + y2) / 2,
                label, fontsize=fontsize, color=color, fontweight="bold",
                ha="center", va="center",
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.85))

# ---- row 1: inputs ---------------------------------------------------------
box(12, 53, 18, 6, "Question $q$", COL_INPUT)
box(34, 53, 18, 6, "Answer $a$", COL_INPUT)
box(56, 53, 18, 6, "Rubric $R$", COL_INPUT)

# ---- row 2: judge panel ----------------------------------------------------
judge_y = 41
n = 4
positions = [10 + i * 12 for i in range(n)]
for i, x in enumerate(positions):
    box(x, judge_y, 10, 5.5, f"$J_{i+1}$\n(SLM)", COL_JUDGE, fontsize=10)

# arrows from inputs to a fan-in, then to each judge
ax.add_patch(FancyArrowPatch((50, 50), (50, 46),
                             arrowstyle="-|>", mutation_scale=14,
                             color=EDGE, linewidth=1.3))
for x in positions:
    arrow(50, 46, x, judge_y + 2.8, curve=0.0, style="-|>")

# ---- row 3: pairwise agreement ---------------------------------------------
box(50, 31, 24, 6, "Pairwise Agreement\n$\\mathrm{Agr}$ (Eq.\\,1)", COL_AGR, fontsize=10)
for x in positions:
    arrow(x, judge_y - 2.8, 50, 34, curve=0.0, style="-|>")

# ---- row 4: threshold decision ---------------------------------------------
arrow(50, 28, 50, 25, style="-|>")
box(50, 22, 32, 5.5,
    "Compare Agr to $\\theta_{FA},\\,\\theta_{MA},\\,\\theta_{SP}$",
    COL_DECIDE, fontsize=9.5)

# branching from decision box
arrow(40, 19.2, 18, 13, curve=0.25, style="-|>")
arrow(60, 19.2, 82, 13, curve=-0.25, style="-|>")

# ---- row 5 (left): DELIBERATION loop ---------------------------------------
box(18, 13, 22, 6,
    "Re-prompt disagreeing\njudges with peer scores",
    COL_DELIB, ec=DELIB_EDGE, fontsize=9)
arrow(18, 10, 18, 8, style="-|>", color=DELIB_EDGE)
box(18, 5, 22, 5.5,
    "Inter-LLM Deliberation\n(EXP5 simulation)",
    COL_DELIB, ec=DELIB_EDGE, fontsize=9)

# feedback arrow from deliberation up to the judges
arrow(28, 7.7, 28, 38.5, curve=0.55, style="-|>",
      color=DELIB_EDGE, lw=1.8)
ax.text(40, 24,
        "Feedback loop:\nresend items that\nare Split or Disagree",
        fontsize=8, color=DELIB_EDGE, fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.3", fc="white",
                  ec=DELIB_EDGE, linewidth=1.0))

# ---- row 5 (right): outcomes ----------------------------------------------
box(82, 13, 22, 4.5,
    "Full Agreement (FA)\nreport $\\hat{S}$",
    COL_OUT_FA, fontsize=8.5)
box(82, 6.5, 22, 4.5,
    "Majority Agreement (MA)\nreport $\\hat{S}$ w/ note",
    COL_OUT_MA, fontsize=8.5)
arrow(82, 4.25, 82, 1.8, style="-|>", color=COL_OUT_DD)
ax.text(82, 0.7,
        "Split (SP) / Disagree (D)  →  human review",
        ha="center", va="center", fontsize=9,
        fontweight="bold", color=COL_OUT_DD)

# title
ax.text(50, 58.5,
        "Multi-SLMs-as-Judge with Inter-LLM Deliberation",
        ha="center", va="center", fontsize=13, fontweight="bold")
ax.text(50, 56.5,
        "Q + A + R  ->  Panel of SLM judges  ->  Pairwise Agr  ->  "
        "Threshold routing  ->  (Re-prompt loop)  ->  Reporting or escalation",
        ha="center", va="center", fontsize=9, color="#334155", style="italic")

plt.tight_layout()
out = "/Users/mahindragupthakotha/Git Repo/multi-slm-judge-bigdata/paper/framework.png"
plt.savefig(out, dpi=200, bbox_inches="tight", facecolor="white")
print("wrote", out)
