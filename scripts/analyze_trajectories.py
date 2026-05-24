"""Categorise the failure mode of every failed Gemini trial.

Reads each trial's gemini-cli.txt transcript and /output/result.* (if any) and
attributes the failure to one of a small set of categories. Output:
  report/data/failure_categorization.csv

Categories:
  - wrong_weight         used WTINT2YR / WTDR2D / unweighted instead of WTMEC2YR/WTDRD1
  - wrong_variable       picked an unrelated variable (BMXHT, RIDRETH3, etc.)
  - list_ordering        right values, wrong order/keys
  - chart_misread        chart-grounded task and definitions mismatch
  - arithmetic_error     correct method, off-by-rounding or sign error
  - format_violation     output not parseable (wrong JSON keys, missing file)
  - design_ignored       used naive binomial SE / no PSU-stratum variance
  - sex_inversion        swapped men/women codes
  - other                catch-all (with verbatim snippet)
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
JOBS = ROOT / "jobs" / "gemini"
OUT = ROOT / "report" / "data" / "failure_categorization.csv"

PATTERNS = [
    ("wrong_weight",    re.compile(r"\bWTINT2YR\b|\bWTDR2D\b|unweighted")),
    ("design_ignored",  re.compile(r"sqrt\(p\s*\*\s*\(1\s*-\s*p\)|binomial.*CI|normal.*approx", re.I)),
    ("sex_inversion",   re.compile(r"RIAGENDR\s*=+\s*1.*female|RIAGENDR\s*=+\s*2.*male", re.I)),
    ("chart_misread",   re.compile(r"could not read the (image|figure|chart|PNG)|skipping the figure", re.I)),
]


def classify_trial(trial_dir: Path, reward: float) -> dict:
    txt_path = trial_dir / "logs" / "agent" / "gemini-cli.txt"
    transcript = txt_path.read_text(errors="replace") if txt_path.exists() else ""
    out_dir = trial_dir / "output"
    result_files = list(out_dir.glob("result.*")) if out_dir.exists() else []
    cat = "other"
    snippet = ""

    if reward >= 1.0:
        cat = "pass"
    elif not result_files:
        cat = "format_violation"
        snippet = "no /output/result.* produced"
    else:
        # Did the output parse?
        try:
            rf = result_files[0]
            text = rf.read_text(errors="replace").strip()
            if rf.suffix == ".json":
                json.loads(text)
        except Exception as e:
            cat = "format_violation"
            snippet = f"output unparseable: {e}"

        if cat == "other":
            for tag, pat in PATTERNS:
                if pat.search(transcript):
                    cat = tag
                    m = pat.search(transcript)
                    if m:
                        start = max(0, m.start() - 30)
                        snippet = transcript[start:m.end() + 40].replace("\n", " ")
                    break

    return {
        "trial": trial_dir.name,
        "reward": reward,
        "category": cat,
        "snippet": snippet[:200],
    }


def main() -> None:
    rows = []
    SELECTED = {
        "task_01_dabstep_5_which-issuing-country-has-the",
        "task_02_dabstep_49_what-is-the-top-country",
        "task_03_dabstep_70_is-martinis-fine-steakhouse-in",
        "task_05_dabstep_1305_for-account-type-h-and",
        "task_10_dabstep_2697_for-belles-cookbook-store-in",
        "task_11_dabstep_orig_belles_total_2023",
        "task_12_dabstep_orig_belles_mcc_counterfactual",
        "task_13_dabstep_orig_fee_ids_nonzero_merchants",
        "task_14_dabstep_orig_crossfit_monthly_sd",
        "task_15_dabstep_orig_lowest_scheme",
    }
    for job_dir in sorted(JOBS.glob("task_*_gemini")):
        task = job_dir.name.replace("_gemini", "")
        if task not in SELECTED:
            continue
        res = json.loads((job_dir / "result.json").read_text())
        evals = res["stats"]["evals"]
        if not evals:
            continue
        ek = next(iter(evals))
        reward_map = {}
        for reward_str, ids in evals[ek].get("reward_stats", {}).get("reward", {}).items():
            for tid in ids:
                reward_map[tid] = float(reward_str)

        for trial in sorted(p for p in job_dir.iterdir() if p.is_dir()):
            r = reward_map.get(trial.name, 0.0)
            info = classify_trial(trial, r)
            info["task"] = task
            rows.append(info)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["task", "trial", "reward", "category", "snippet"])
        for r in rows:
            w.writerow([r["task"], r["trial"], r["reward"], r["category"], r["snippet"]])

    from collections import Counter
    c = Counter(r["category"] for r in rows if r["category"] != "pass")
    total_fail = sum(c.values())
    print(f"Categorised {len(rows)} trials; {total_fail} failures")
    for cat, n in c.most_common():
        print(f"  {cat:20s} {n:3d}  ({100*n/max(1,total_fail):.1f}%)")
    print(f"\nWrote {OUT}")


if __name__ == "__main__":
    main()
