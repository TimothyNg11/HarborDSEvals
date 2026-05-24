"""Generate the three figures referenced in the report:

  - report/figures/difficulty_curve.png
  - report/figures/failure_taxonomy.png
  - report/figures/pass_rate_by_axis.png

All numbers come from
  report/data/pass_at_k_results.csv
  report/data/failure_categorization.csv

Both inputs must exist; run scripts/compute_pass_at_k.py and
scripts/analyze_trajectories.py first.
"""
from __future__ import annotations

import csv
import subprocess
import sys
from collections import Counter
from pathlib import Path

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "matplotlib"])
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
PASSK = ROOT / "report" / "data" / "pass_at_k_results.csv"
FAILS = ROOT / "report" / "data" / "failure_categorization.csv"
FIG_DIR = ROOT / "report" / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

# Map task to the dominant difficulty axis(es) listed in task.toml.
AXIS = {
    "task_01_dabstep_5_which-issuing-country-has-the":   "lookup",
    "task_02_dabstep_49_what-is-the-top-country":        "lookup",
    "task_03_dabstep_70_is-martinis-fine-steakhouse-in": "semantic",
    "task_05_dabstep_1305_for-account-type-h-and":       "multi_filter_precision",
    "task_10_dabstep_2697_for-belles-cookbook-store-in": "combinatorial",
    "task_11_dabstep_orig_belles_total_2023":            "multi_filter_precision",
    "task_12_dabstep_orig_belles_mcc_counterfactual":    "counterfactual",
    "task_13_dabstep_orig_fee_ids_nonzero_merchants":    "long_list",
    "task_14_dabstep_orig_crossfit_monthly_sd":          "statistical",
    "task_15_dabstep_orig_lowest_scheme":                "argmin_compound",
}


def read_pa():
    rows = []
    with PASSK.open() as f:
        for r in csv.DictReader(f):
            if r.get("task", "").startswith("task_"):
                r["pass_at_1"] = float(r["pass_at_1"])
                r["pass_at_3"] = float(r["pass_at_3"])
                rows.append(r)
    return rows


def difficulty_curve(rows):
    fig, ax = plt.subplots(figsize=(9.5, 4.6), dpi=140)
    xs = list(range(1, len(rows) + 1))
    p1 = [r["pass_at_1"] for r in rows]
    p3 = [r["pass_at_3"] for r in rows]
    ax.plot(xs, p1, "o-", color="#3b6ad6", linewidth=2, label="pass@1")
    ax.plot(xs, p3, "s--", color="#d6573b", linewidth=2, label="pass@3")
    ax.set_xticks(xs)
    ax.set_xticklabels([f"T{n:02d}" for n in xs], fontsize=9)
    ax.set_ylim(-0.05, 1.05)
    ax.set_ylabel("Reward")
    ax.set_xlabel("Task (in curriculum order)")
    ax.set_title("Difficulty curve — gemini-3-flash-preview, 3 attempts per task")
    ax.grid(alpha=0.3)
    ax.legend(loc="upper right")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "difficulty_curve.png", facecolor="white")
    plt.close(fig)
    print("  wrote difficulty_curve.png")


def failure_taxonomy():
    cats = Counter()
    with FAILS.open() as f:
        for r in csv.DictReader(f):
            if r["category"] != "pass":
                cats[r["category"]] += 1
    if not cats:
        print("  no failures to plot, skipping failure_taxonomy")
        return
    labels, counts = zip(*cats.most_common())
    colors = ["#d6573b", "#d6a32b", "#3b6ad6", "#2bb673", "#a04ad6",
              "#7a7e91", "#4a8fb3", "#b3754a"]
    fig, ax = plt.subplots(figsize=(7.5, 6), dpi=140)
    wedges, _texts, autotexts = ax.pie(
        counts, labels=labels, colors=colors[: len(labels)],
        autopct="%1.0f%%", textprops={"fontsize": 10},
        wedgeprops={"linewidth": 1.5, "edgecolor": "white"},
    )
    for t in autotexts:
        t.set_color("white")
        t.set_fontweight("bold")
    ax.set_title("Failure-mode taxonomy (gemini-3-flash-preview)")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "failure_taxonomy.png", facecolor="white")
    plt.close(fig)
    print("  wrote failure_taxonomy.png")


def pass_rate_by_axis(rows):
    buckets = {}
    for r in rows:
        a = AXIS.get(r["task"], "other")
        buckets.setdefault(a, []).append(r["pass_at_3"])
    order = ["lookup", "semantic", "multi_filter_precision", "counterfactual",
             "long_list", "statistical", "argmin_compound", "combinatorial"]
    labels = [a for a in order if a in buckets]
    if not labels:
        labels = list(buckets.keys())
    means = [sum(buckets[a]) / len(buckets[a]) for a in labels]
    counts = [len(buckets[a]) for a in labels]

    fig, ax = plt.subplots(figsize=(9, 4.6), dpi=140)
    colors = ["#7a7e91", "#3b6ad6", "#2bb673", "#d6a32b", "#d6573b"][: len(labels)]
    bars = ax.bar(labels, means, color=colors, edgecolor="black", linewidth=1.2)
    for b, m, n in zip(bars, means, counts):
        ax.text(b.get_x() + b.get_width() / 2, m + 0.02,
                f"{100 * m:.0f}%  (n={n})", ha="center", fontsize=10)
    ax.set_ylim(0, max(1.0, (max(means) if means else 1.0) * 1.2))
    ax.set_ylabel("pass@3")
    ax.set_title("pass@3 by difficulty axis")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "pass_rate_by_axis.png", facecolor="white")
    plt.close(fig)
    print("  wrote pass_rate_by_axis.png")


def main():
    rows = read_pa()
    difficulty_curve(rows)
    failure_taxonomy()
    pass_rate_by_axis(rows)


if __name__ == "__main__":
    main()
