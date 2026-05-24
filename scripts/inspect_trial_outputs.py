"""For every completed Gemini trial, print the agent's final /output/ file
contents and a 1-line summary. Useful for spot-checking why specific trials
passed or failed.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
JOBS = ROOT / "jobs" / "gemini"


def main():
    for job in sorted(JOBS.glob("task_*_gemini")):
        task = job.name.replace("_gemini", "")
        result_file = job / "result.json"
        if not result_file.exists():
            continue
        result = json.loads(result_file.read_text())
        evals = result["stats"]["evals"]
        if not evals:
            continue
        ek = next(iter(evals))
        rewards = evals[ek].get("reward_stats", {}).get("reward", {})
        reward_map = {}
        for r_str, ids in rewards.items():
            for tid in ids:
                reward_map[tid] = float(r_str)

        print(f"\n=== {task} ===")
        for tr in sorted(p for p in job.iterdir() if p.is_dir()):
            r = reward_map.get(tr.name, "pending")
            # Find /output files in the trial
            agent_log = tr / "agent" / "gemini-cli.txt"
            # Heuristic: extract last result.txt or result.json from transcript
            if agent_log.exists():
                text = agent_log.read_text(errors="replace")
                # Find last `to /output/result` mention
                marker = None
                for m in ("/output/result.json", "/output/result.txt"):
                    idx = text.rfind(m)
                    if idx != -1:
                        marker = idx
                end = min(len(text), (marker or 0) + 600)
                snippet = text[max(0, (marker or 0) - 100):end].replace("\n", " ")[:500] if marker else text[-300:].replace("\n", " ")
            else:
                snippet = "<no transcript>"
            print(f"  {tr.name[-10:]}  reward={r}  ...{snippet[-300:]}")


if __name__ == "__main__":
    main()
