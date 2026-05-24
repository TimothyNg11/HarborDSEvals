"""Compute per-task and aggregate pass@1 and pass@3 from harbor job results.

Reads:
  jobs/gemini/<task>_gemini/result.json  (one per task; each is a k=3 job)
Writes:
  report/data/pass_at_k_results.csv

Also prints a markdown table to stdout suitable for embedding in the report.
"""
from __future__ import annotations

import csv
import glob
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
JOBS = ROOT / "jobs" / "gemini"
OUT_CSV = ROOT / "report" / "data" / "pass_at_k_results.csv"


def main() -> None:
    rows = []
    SELECTED = {
        "task_03_dabstep_70_is-martinis-fine-steakhouse-in",
        "task_05_dabstep_1305_for-account-type-h-and",
        "task_06_dabstep_1464_what-is-the-fee-id",
        "task_09_dabstep_1871_in-january-what-delta-would",
        "task_10_dabstep_2697_for-belles-cookbook-store-in",
        "task_11_dabstep_orig_belles_total_2023",
        "task_12_dabstep_orig_belles_mcc_counterfactual",
        "task_14_dabstep_orig_crossfit_monthly_sd",
    }
    for job_dir in sorted(JOBS.glob("task_*_gemini")):
        task = job_dir.name.replace("_gemini", "")
        if task not in SELECTED:
            continue
        result = job_dir / "result.json"
        if not result.exists():
            print(f"WARN missing {result}")
            continue
        data = json.loads(result.read_text())
        evals = data["stats"]["evals"]
        if not evals:
            continue
        ek = next(iter(evals))
        rs = evals[ek].get("reward_stats", {}).get("reward", {})
        rewards = []
        for reward_str, ids in rs.items():
            for _ in ids:
                rewards.append(float(reward_str))
        n_trials = len(rewards)
        # pass@1 = mean reward across trials (each trial is independent attempt)
        pass_at_1 = sum(rewards) / n_trials if n_trials else 0.0
        pass_at_3 = 1.0 if any(r > 0 for r in rewards) else 0.0
        rows.append(dict(
            task=task,
            n_trials=n_trials,
            rewards=rewards,
            pass_at_1=pass_at_1,
            pass_at_3=pass_at_3,
        ))

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["task", "n_trials", "rewards", "pass_at_1", "pass_at_3"])
        for r in rows:
            w.writerow([
                r["task"],
                r["n_trials"],
                "|".join(str(int(x)) for x in r["rewards"]),
                f"{r['pass_at_1']:.3f}",
                f"{r['pass_at_3']:.3f}",
            ])

    if not rows:
        print("no results to aggregate")
        return

    agg_pa1 = sum(r["pass_at_1"] for r in rows) / len(rows)
    agg_pa3 = sum(r["pass_at_3"] for r in rows) / len(rows)
    print("| Task | trials | pass@1 | pass@3 |")
    print("|------|--------|--------|--------|")
    for r in rows:
        print(f"| {r['task']} | {r['rewards']} | {r['pass_at_1']:.2f} | {r['pass_at_3']:.2f} |")
    print(f"\nAggregate pass@1: {100 * agg_pa1:.1f}%")
    print(f"Aggregate pass@3: {100 * agg_pa3:.1f}%")
    print(f"\nWrote {OUT_CSV}")


if __name__ == "__main__":
    main()
