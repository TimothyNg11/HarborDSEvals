"""Generate result figures from the aggregated results/.

Outputs:
- report/figures/multimodel_heatmap.png  — 2 × 10 task × model pass@3 heatmap.
- report/figures/intervention_delta.png  — paired bar chart of baseline vs
  intervention pass@3 for T05–T09, both models.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
FIGS = ROOT / "report" / "figures"
FIGS.mkdir(parents=True, exist_ok=True)

TASKS = [f"T{i:02d}" for i in range(1, 11)]
INTV_TASKS = ["T05", "T06", "T07", "T08", "T09"]


def pa3(rewards):
    return 1.0 if any(r == 1.0 for r in rewards) else 0.0


def count_pass(rewards):
    return sum(1 for r in rewards if r == 1.0)


def main():
    data = json.load(open(RESULTS / "per_task_rewards.json"))

    # --- Multimodel heatmap (pass@3 as 0/3, 1/3, 2/3, 3/3) ---
    matrix = np.zeros((2, len(TASKS)))   # row 0 = gemini, row 1 = haiku
    for j, t in enumerate(TASKS):
        gr = data.get(t, {}).get("gemini_baseline", [])
        hr = data.get(t, {}).get("haiku_baseline", [])
        # Use proportion of trials passing (0, 1/3, 2/3, 1.0) — finer signal than just pass@3
        matrix[0, j] = (count_pass(gr) / 3.0) if gr else np.nan
        matrix[1, j] = (count_pass(hr) / 3.0) if hr else np.nan

    fig, ax = plt.subplots(figsize=(11, 2.6))
    im = ax.imshow(matrix, cmap="RdYlGn", vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(len(TASKS)), TASKS)
    ax.set_yticks([0, 1], ["gemini-3-flash", "haiku-4.5"])
    ax.set_title("Multi-model baseline: proportion of trials passing (n=3)")
    # Cell annotations
    for i in range(2):
        for j in range(len(TASKS)):
            val = matrix[i, j]
            if np.isnan(val):
                label = "—"
            else:
                label = f"{int(val*3)}/3"
            ax.text(j, i, label, ha="center", va="center",
                    color="black", fontsize=10)
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label="pass rate (n=3)")
    fig.tight_layout()
    out = FIGS / "multimodel_heatmap.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"wrote {out}")

    # --- Intervention paired bar chart ---
    width = 0.18
    x = np.arange(len(INTV_TASKS))
    fig, ax = plt.subplots(figsize=(10, 4.5))

    def trials_passing(arr):
        return count_pass(arr) if arr else 0

    g_base = [trials_passing(data.get(t, {}).get("gemini_baseline", []))      for t in INTV_TASKS]
    h_base = [trials_passing(data.get(t, {}).get("haiku_baseline",  []))      for t in INTV_TASKS]
    g_intv = [trials_passing(data.get(t, {}).get("gemini_intervention", []))  for t in INTV_TASKS]
    h_intv = [trials_passing(data.get(t, {}).get("haiku_intervention",  []))  for t in INTV_TASKS]

    # Convert counts to pass-rate (out of 3)
    g_base_r = [v / 3.0 for v in g_base]
    h_base_r = [v / 3.0 for v in h_base]
    g_intv_r = [v / 3.0 for v in g_intv]
    h_intv_r = [v / 3.0 for v in h_intv]

    b1 = ax.bar(x - 1.5 * width, g_base_r, width, label="gemini-3-flash (baseline)",
                color="#4c72b0", hatch="")
    b2 = ax.bar(x - 0.5 * width, g_intv_r, width, label="gemini-3-flash (intervention)",
                color="#4c72b0", hatch="///")
    b3 = ax.bar(x + 0.5 * width, h_base_r, width, label="haiku-4.5 (baseline)",
                color="#dd8452", hatch="")
    b4 = ax.bar(x + 1.5 * width, h_intv_r, width, label="haiku-4.5 (intervention)",
                color="#dd8452", hatch="///")

    # Annotate each bar with the raw count
    def annotate(bars, counts):
        for bar, c in zip(bars, counts):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02,
                    f"{c}/3", ha="center", va="bottom", fontsize=8)
    annotate(b1, g_base)
    annotate(b2, g_intv)
    annotate(b3, h_base)
    annotate(b4, h_intv)

    ax.set_xticks(x, INTV_TASKS)
    ax.set_ylabel("pass rate (n=3 trials)")
    ax.set_ylim(0, 1.15)
    ax.set_title("Rule-precedence prompt intervention: baseline vs. intervention pass rate")
    ax.legend(loc="upper left", ncol=2, frameon=False, fontsize=9)
    ax.spines[["right", "top"]].set_visible(False)
    fig.tight_layout()
    out = FIGS / "intervention_delta.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
