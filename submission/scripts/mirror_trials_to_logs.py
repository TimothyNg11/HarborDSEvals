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
        "logs/agent/gemini-cli.txt",
        "logs/verifier/reward.txt",
        "logs/verifier/reward.json",
        "logs/verifier/ctrf.json",
        "exception.txt",
        "trial.log",
    ):
        s = src / rel
        if s.exists():
            d = dst / rel
            d.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(s, d)


def main():
    LOGS.mkdir(exist_ok=True)
    for job in sorted(JOBS.glob("task_*_gemini")):
        task = job.name.replace("_gemini", "")
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
