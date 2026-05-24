"""Corrected failure-mode pie chart.

The original chart in report/figures/failure_taxonomy.png categorises by
surface symptom: semantic_miss, multi_filter_precision, implicit_rule_miss,
counterfactual_planning, combinatorial_planning, rule_overlap_misread.

A trajectory-level reread shows three of those share a root cause:
multi_filter_precision (T05), implicit_rule_miss (T06), and
counterfactual_planning (T09) are all Gemini applying a "most-specific
matching rule wins" precedence policy in violation of the manual, which
explicitly says every matching rule applies and that empty/null fields mean
"any value."

This script produces a 4-slice corrected pie that collapses those into one
"Rule-precedence misread" slice. The dominant slice is ~47%.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "report" / "figures" / "failure_taxonomy_v2.png"
OUT.parent.mkdir(parents=True, exist_ok=True)

# Failures across the 8 selected tasks (24 trials, 19 failures).
slices = [
    ("Rule-precedence misread\n(T05, T06, T09)",        9, "#d6573b"),
    ("Monthly-bucket micro-bug\n(T12 trial 1, T14)",    4, "#3b6ad6"),
    ("Question-premise blindness\n(T03)",               3, "#d6a32b"),
    ("Search-space pruning\n(T10)",                     3, "#2bb673"),
]
labels = [s[0] for s in slices]
counts = [s[1] for s in slices]
colors = [s[2] for s in slices]

fig, ax = plt.subplots(figsize=(8.5, 6.5), dpi=140)
wedges, _texts, autotexts = ax.pie(
    counts,
    labels=labels,
    colors=colors,
    autopct=lambda p: f"{p:.0f}%\n({int(round(p * sum(counts) / 100))} trials)",
    startangle=90,
    counterclock=False,
    textprops={"fontsize": 10},
    wedgeprops={"linewidth": 1.5, "edgecolor": "white"},
)
for t in autotexts:
    t.set_color("white")
    t.set_fontweight("bold")
    t.set_fontsize(9)

ax.set_title(
    "Failure-mode taxonomy — root-cause view\n"
    "gemini-3-flash-preview, 19 failed trials across 8 tasks",
    fontsize=11,
)
fig.tight_layout()
fig.savefig(OUT, facecolor="white")
plt.close(fig)
print(f"wrote {OUT}")
