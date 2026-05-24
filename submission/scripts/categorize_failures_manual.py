"""Hand-curated failure-mode categorisation for the final 10 trials.

The auto-categoriser is naive — it classes everything as `format_violation`
because every failed trial writes a final `answer.txt` but the answer is
substantively wrong. The real failure modes (which I documented in the
report) are taxonomy I derived from reading the gemini-cli transcripts and
comparing the predicted answers against the ground-truth answers.

This script writes a corrected `failure_categorization.csv` that the report
references.
"""
from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "report" / "data" / "failure_categorization.csv"

# task -> failure category for its failing trials. Tasks with mixed pass/fail
# have only their failed trials' category recorded.
TASK_FAILURE_MODE = {
    # DABstep
    "task_01_dabstep_5_which-issuing-country-has-the":   None,           # 3/3 pass
    "task_02_dabstep_49_what-is-the-top-country":        "format_violation",  # 1 fail: wrong multi-choice format
    "task_03_dabstep_70_is-martinis-fine-steakhouse-in": "semantic_miss", # said yes/no, truth is "Not Applicable"
    "task_05_dabstep_1305_for-account-type-h-and":       "multi_filter_precision",   # wrong rule subset
    "task_10_dabstep_2697_for-belles-cookbook-store-in": "combinatorial_planning",   # picked wrong ACI
    # Original
    "task_11_dabstep_orig_belles_total_2023":            "rule_overlap_misread",     # 73% over truth: double-summing
    "task_12_dabstep_orig_belles_mcc_counterfactual":    "counterfactual_planning",   # never recomputed
    "task_13_dabstep_orig_fee_ids_nonzero_merchants":    "implicit_rule_miss",       # most-specific match interpretation
    "task_14_dabstep_orig_crossfit_monthly_sd":          "rule_overlap_misread",     # bad upstream fee sum
    "task_15_dabstep_orig_lowest_scheme":                "compound_format_or_precision",
}

# Trial counts and observed reward per trial, gathered from pass_at_k_results.csv.
TRIAL_REWARDS = {
    "task_01_dabstep_5_which-issuing-country-has-the":   [1, 1, 1],
    "task_02_dabstep_49_what-is-the-top-country":        [1, 1, 0],
    "task_03_dabstep_70_is-martinis-fine-steakhouse-in": [0, 0, 0],
    "task_05_dabstep_1305_for-account-type-h-and":       [0, 0, 0],
    "task_10_dabstep_2697_for-belles-cookbook-store-in": [0, 0, 0],
    "task_11_dabstep_orig_belles_total_2023":            [0, 0, 0],
    "task_12_dabstep_orig_belles_mcc_counterfactual":    [0, 0, 0],
    "task_13_dabstep_orig_fee_ids_nonzero_merchants":    [0, 0, 0],
    "task_14_dabstep_orig_crossfit_monthly_sd":          [0, 0, 0],
    "task_15_dabstep_orig_lowest_scheme":                [0, 0, 0],
}


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["task", "trial", "reward", "category", "snippet"])
        for task, rewards in TRIAL_REWARDS.items():
            for i, r in enumerate(rewards, 1):
                cat = "pass" if r == 1 else TASK_FAILURE_MODE.get(task, "other")
                w.writerow([task, f"trial_{i}", r, cat, ""])
    print(f"Wrote {OUT}")
    # Print summary
    from collections import Counter
    c = Counter()
    for task, rewards in TRIAL_REWARDS.items():
        for r in rewards:
            cat = "pass" if r == 1 else TASK_FAILURE_MODE.get(task, "other")
            c[cat] += 1
    total = sum(c.values())
    for cat, n in c.most_common():
        print(f"  {cat:30s} {n:3d}  ({100*n/total:.1f}%)")


if __name__ == "__main__":
    main()
