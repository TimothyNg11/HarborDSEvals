"""Mirror jobs/gemini/<task>_gemini/ trial directories into the spec's
required layout:  logs/<task>/trial_<n>/<trial_stuff>.

Only the agent transcript, verifier reward, and exception (if any) are
copied; the bulky Docker artifacts stay in jobs/.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
JOBS = ROOT / "jobs" / "gemini"
LOGS = ROOT / "logs"


def copy_artifacts(src: Path, dst: Path) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    for rel in (
        "agent/gemini-cli.txt",
        "agent/gemini-cli.trajectory.jsonl",
        "agent/trajectory.json",
        "verifier/reward.txt",
        "verifier/reward.json",
        "verifier/ctrf.json",
        "verifier/test-stdout.txt",
        "config.json",
        "result.json",
        "exception.txt",
        "trial.log",
    ):
        s = src / rel
        if s.exists():
            d = dst / rel
            d.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(s, d)


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


def main():
    LOGS.mkdir(exist_ok=True)
    for job in sorted(JOBS.glob("task_*_gemini")):
        task = job.name.replace("_gemini", "")
        if task not in SELECTED:
            continue
        result_file = job / "result.json"
        if not result_file.exists():
            continue
        result = json.loads(result_file.read_text())
        evals = result["stats"]["evals"]
        if not evals:
            continue  # job still in progress
        ek = next(iter(evals))
        # Map trial id -> reward.
        reward_map = {}
        for reward_str, ids in evals[ek].get("reward_stats", {}).get("reward", {}).items():
            for tid in ids:
                reward_map[tid] = float(reward_str)

        trial_dirs = sorted(p for p in job.iterdir() if p.is_dir())
        out_root = LOGS / task
        out_root.mkdir(exist_ok=True)
        # Also copy job-level result.json for quick reference.
        shutil.copy(result_file, out_root / "result.json")

        for i, td in enumerate(trial_dirs, 1):
            tdst = out_root / f"trial_{i}"
            copy_artifacts(td, tdst)
            r = reward_map.get(td.name, 0.0)
            (tdst / "reward.txt").write_text(str(r))
            print(f"  mirrored {task}/trial_{i}: reward={r}")


if __name__ == "__main__":
    main()
