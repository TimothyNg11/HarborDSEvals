"""End-of-pipeline: ingest completed trial results, generate every artifact
the report references, splice the per-task table back into report.md, and
print a final summary.

Idempotent — safe to re-run after partial trials finish.
"""
from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run(cmd: list[str], label: str) -> None:
    print(f"\n=== {label} ===")
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    print(r.stdout[-1500:] if r.stdout else "")
    if r.returncode != 0:
        print(r.stderr[-1500:], file=sys.stderr)


def splice_report_table() -> None:
    """Replace the placeholder per-task row with computed values."""
    csv_path = ROOT / "report" / "data" / "pass_at_k_results.csv"
    if not csv_path.exists():
        return
    rows = list(csv.DictReader(csv_path.open()))
    if not rows:
        return
    lines = ["| Task | rewards (per trial) | pass@1 | pass@3 |",
             "|------|---------------------|--------|--------|"]
    for r in rows:
        rewards = r["rewards"].replace("|", ", ")
        lines.append(
            f"| {r['task']} | [{rewards}] | {float(r['pass_at_1']):.2f} | {float(r['pass_at_3']):.2f} |"
        )
    agg_pa1 = sum(float(r["pass_at_1"]) for r in rows) / len(rows)
    agg_pa3 = sum(float(r["pass_at_3"]) for r in rows) / len(rows)
    lines.append("")
    lines.append(f"**Aggregate pass@1: {100 * agg_pa1:.1f}% — Aggregate pass@3: {100 * agg_pa3:.1f}%**")
    new_table = "\n".join(lines)

    report = ROOT / "report" / "report.md"
    text = report.read_text(encoding="utf-8")
    start = text.find("| Task | rewards (per trial) | pass@1 | pass@3 |")
    if start == -1:
        # Find placeholder
        start = text.find("| Task | rewards")
    if start == -1:
        print("could not splice — placeholder not found")
        return
    end = text.find("\n\n", start)
    end = end if end != -1 else len(text)
    new_text = text[:start] + new_table + text[end:]
    # Also splice aggregate sentence
    new_text = new_text.replace(
        "**Aggregate `pass@3` across all 10 tasks: see report/data/pass_at_k_results.csv**",
        f"**Aggregate `pass@3` across all 10 tasks: {100 * agg_pa3:.1f}%** "
        f"(pass@1 = {100 * agg_pa1:.1f}%; n_tasks={len(rows)}, 3 attempts each).",
    )
    report.write_text(new_text, encoding="utf-8")
    print("spliced report.md table")


def main() -> None:
    run([sys.executable, "scripts/mirror_trials_to_logs.py"],   "mirror to logs/")
    run([sys.executable, "scripts/compute_pass_at_k.py"],       "compute pass@k")
    run([sys.executable, "scripts/analyze_trajectories.py"],    "categorise failures")
    run([sys.executable, "scripts/generate_report_figures.py"], "generate plots")
    splice_report_table()
    print("\nDone. Report at report/report.md")


if __name__ == "__main__":
    main()
