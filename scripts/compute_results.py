"""Aggregate Harbor trial results into CSVs and per-task rewards tables.

Produces three artifacts:

1. results/multimodel_baseline.csv  — task × {gemini, haiku} pass@1 / pass@3
2. results/intervention.csv         — paired baseline vs intervention pass@3
                                       (raw rewards from the 30 intervention
                                       trials + the 30 already-finished
                                       baseline trials), with delta_pp.
3. results/per_task_rewards.json    — full rewards array per (task, model,
                                       condition) for downstream plotting.

pass@1 is the FIRST trial's reward (not the mean — that's a noisier estimate
of how often the model gets it right on the first shot). pass@3 is whether
ANY trial out of 3 passed.
"""
from __future__ import annotations

import csv
import glob
import json
import os
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
RESULTS.mkdir(exist_ok=True)

# Task id -> short label (T01..T10)
TASK_LABELS = {f"task_{i:02d}": f"T{i:02d}" for i in range(1, 11)}

INTERVENTION_TASKS = {f"T0{i}" for i in (5, 6, 7, 8, 9)}


def load_rewards(result_json_path: str) -> list[float]:
    """Extract the rewards array from one Harbor job's result.json.

    Pads with 0.0 for any errored trials (an error counts as a failure for
    pass@k purposes, not a missing data point). Returns an empty list if the
    job didn't complete enough to record any results yet.
    """
    r = json.load(open(result_json_path))
    stats = r.get("stats", {})
    evals = stats.get("evals", {})
    if not evals:
        return []
    ek = next(iter(evals))
    rs = evals[ek].get("reward_stats", {}).get("reward", {})
    rewards: list[float] = []
    for reward_str, ids in rs.items():
        for _ in ids:
            rewards.append(float(reward_str))
    # Pad with 0.0 for errored trials (no reward recorded but counts as fail).
    # n_total_trials is the target k; rewards has only successful-completion
    # entries, so the gap == number of errored trials.
    n_total = r.get("n_total_trials") or stats.get("n_completed_trials", 0)
    while len(rewards) < n_total:
        rewards.append(0.0)
    return rewards


def collect_arm(jobs_glob: str, strip_suffix: str) -> dict[str, list[float]]:
    """Return {short_task_label: [rewards]} for one job-dir arm."""
    out: dict[str, list[float]] = {}
    for f in sorted(glob.glob(jobs_glob)):
        job_name = os.path.basename(os.path.dirname(f))
        task_full = job_name.removesuffix(strip_suffix)
        # task_full looks like 'task_05_dabstep_1305_for-account-type-h-and'
        # Extract the 'task_05' prefix
        prefix = "_".join(task_full.split("_")[:2])
        label = TASK_LABELS.get(prefix)
        if label is None:
            continue
        out[label] = load_rewards(f)
    return out


def pa1(rewards: list[float]) -> float:
    return float(rewards[0]) if rewards else 0.0


def pa3(rewards: list[float]) -> float:
    return 1.0 if any(r == 1.0 for r in rewards) else 0.0


def main():
    gemini = collect_arm(str(ROOT / "jobs/gemini/*_gemini/result.json"), "_gemini")
    haiku = collect_arm(str(ROOT / "jobs/haiku/*_haiku/result.json"), "_haiku")
    intv_gemini = collect_arm(
        str(ROOT / "jobs/intervention_gemini/*_intv_gemini/result.json"),
        "_intv_gemini",
    )
    intv_haiku = collect_arm(
        str(ROOT / "jobs/intervention_haiku/*_intv_haiku/result.json"),
        "_intv_haiku",
    )

    # --- multimodel_baseline.csv ---
    mm_path = RESULTS / "multimodel_baseline.csv"
    with open(mm_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["task_id", "gemini_pa1", "gemini_pa3", "haiku_pa1", "haiku_pa3"])
        agg = defaultdict(float)
        n = 0
        for tid in sorted(TASK_LABELS.values()):
            gr = gemini.get(tid, [])
            hr = haiku.get(tid, [])
            row = [tid, pa1(gr), pa3(gr), pa1(hr), pa3(hr)]
            w.writerow(row)
            for k, v in zip(["gemini_pa1", "gemini_pa3", "haiku_pa1", "haiku_pa3"], row[1:]):
                agg[k] += float(v)
            n += 1
        if n:
            w.writerow(["AGGREGATE"] + [f"{agg[k]/n:.4f}" for k in
                ["gemini_pa1", "gemini_pa3", "haiku_pa1", "haiku_pa3"]])
    print(f"wrote {mm_path}")

    # --- intervention.csv ---
    iv_path = RESULTS / "intervention.csv"
    with open(iv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["task_id", "model", "baseline_pa3", "intervention_pa3", "delta_pp"])
        agg = defaultdict(lambda: {"b": 0.0, "i": 0.0, "n": 0})
        for tid in sorted(INTERVENTION_TASKS):
            for model, base_arm, intv_arm in [
                ("gemini-3-flash", gemini, intv_gemini),
                ("haiku-4-5", haiku, intv_haiku),
            ]:
                base_p = pa3(base_arm.get(tid, []))
                intv_p = pa3(intv_arm.get(tid, []))
                delta = (intv_p - base_p) * 100  # pp
                w.writerow([tid, model, base_p, intv_p, f"{delta:+.1f}"])
                agg[model]["b"] += base_p
                agg[model]["i"] += intv_p
                agg[model]["n"] += 1
        for model in ("gemini-3-flash", "haiku-4-5"):
            d = agg[model]
            if d["n"]:
                b = d["b"] / d["n"]
                i = d["i"] / d["n"]
                w.writerow([f"AGGREGATE-{model}", model,
                            f"{b:.4f}", f"{i:.4f}", f"{(i-b)*100:+.1f}"])
    print(f"wrote {iv_path}")

    # --- per_task_rewards.json ---
    per_task = {}
    for tid in sorted(TASK_LABELS.values()):
        per_task[tid] = {
            "gemini_baseline": gemini.get(tid, []),
            "haiku_baseline": haiku.get(tid, []),
            "gemini_intervention": intv_gemini.get(tid, []),
            "haiku_intervention": intv_haiku.get(tid, []),
        }
    rj = RESULTS / "per_task_rewards.json"
    rj.write_text(json.dumps(per_task, indent=2), encoding="utf-8")
    print(f"wrote {rj}")

    # Print summary
    print()
    print("--- Per-task summary ---")
    print(f"{'task':<6} {'gemini':>10} {'haiku':>10} {'g-intv':>10} {'h-intv':>10}")
    for tid in sorted(TASK_LABELS.values()):
        gr = gemini.get(tid, [])
        hr = haiku.get(tid, [])
        gi = intv_gemini.get(tid, [])
        hi = intv_haiku.get(tid, [])
        def s(r):
            if not r:
                return " — "
            n = sum(1 for x in r if x == 1.0)
            return f"{n}/{len(r)}"
        print(f"{tid:<6} {s(gr):>10} {s(hr):>10} {s(gi):>10} {s(hi):>10}")


if __name__ == "__main__":
    main()
