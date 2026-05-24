"""Inject result numbers into paper/main.tex placeholder blocks.

Reads:
- results/multimodel_baseline.csv
- results/intervention.csv

Replaces the [BASELINE_TABLE_PLACEHOLDER ...] and [INTERVENTION_TABLE_PLACEHOLDER ...]
comment blocks in paper/main.tex with rendered tabular rows. Idempotent: re-running
overwrites the previously injected block.
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAPER = ROOT / "paper" / "main.tex"
MM_CSV = ROOT / "results" / "multimodel_baseline.csv"
IV_CSV = ROOT / "results" / "intervention.csv"

# Task labels in the paper
TASK_DESC = {
    "T01": "T01 (issuing country)",
    "T02": "T02 (top fraud country)",
    "T03": "T03 (semantic Martinis)",
    "T04": "T04 (avg fee credit)",
    "T05": "T05 (avg fee H+MCC+scheme)",
    "T06": "T06 (fee IDs R+B)",
    "T07": "T07 (fee IDs Belles day 10)",
    "T08": "T08 (fee IDs Belles March)",
    "T09": "T09 (counterfactual delta)",
    "T10": "T10 (ACI optimization)",
}


def n_pass(rewards_count_str: str) -> str:
    """Convert pa3 float (e.g. '1.0', '0.0') to '3/3' or '0/3' display."""
    try:
        v = float(rewards_count_str)
    except ValueError:
        return rewards_count_str
    # pa3 is binary 0/1 in our CSVs; for per-trial count, look at the raw rewards JSON
    return f"{int(v * 3)}/3" if v in (0.0, 1.0, 1/3, 2/3) else f"{v:.2f}"


def render_baseline_table() -> str:
    rows = []
    aggregate = None
    with open(MM_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            tid = r["task_id"]
            if tid.startswith("AGGREG"):
                aggregate = r
                continue
            desc = TASK_DESC.get(tid, tid)
            # We need per-trial counts. multimodel_baseline.csv has pa3 (binary).
            # For per-trial counts we need to read per_task_rewards.json. Easier
            # to do a lookup table.
            rows.append((tid, desc, r["gemini_pa3"], r["haiku_pa3"]))
    # Pull per-trial counts from per_task_rewards.json
    import json
    per_task = json.load(open(ROOT / "results" / "per_task_rewards.json"))

    def count_pass(arr):
        return sum(1 for x in arr if x == 1.0) if arr else 0

    out_lines = []
    for tid, desc, _, _ in rows:
        gb = count_pass(per_task.get(tid, {}).get("gemini_baseline", []))
        hb = count_pass(per_task.get(tid, {}).get("haiku_baseline", []))
        gd = "{}/3".format(gb) if per_task.get(tid, {}).get("gemini_baseline") else "—"
        hd = "{}/3".format(hb) if per_task.get(tid, {}).get("haiku_baseline") else "—"
        out_lines.append(f"{desc} & {gd} & {hd} \\\\")
    if aggregate is not None:
        # Aggregate pass@3 across all 10 tasks
        ga = float(aggregate["gemini_pa3"]) * 100
        ha = float(aggregate["haiku_pa3"]) * 100
        out_lines.append("\\midrule")
        out_lines.append(f"Aggregate pass@3 & {ga:.0f}\\% & {ha:.0f}\\% \\\\")
    return "\n".join(out_lines)


def render_intervention_table() -> str:
    rows = []
    aggs = []
    with open(IV_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            if r["task_id"].startswith("AGGREG"):
                aggs.append(r)
    lines = []
    name_map = {"gemini-3-flash": r"\texttt{gemini-3-flash}",
                "haiku-4-5":      r"\texttt{haiku-4.5}"}
    for r in aggs:
        m = name_map.get(r["model"], r["model"])
        b = float(r["baseline_pa3"]) * 100
        i = float(r["intervention_pa3"]) * 100
        d = r["delta_pp"]
        lines.append(f"{m} & {b:.0f}\\% & {i:.0f}\\% & {d}~pp \\\\")
    return "\n".join(lines)


def main():
    paper = PAPER.read_text(encoding="utf-8")
    bt = render_baseline_table()
    it = render_intervention_table()

    # Replace the baseline placeholder lines. Use lambda for repl so \-escapes
    # in the replacement aren't reinterpreted by re.sub.
    bt_replacement = (
        "% [BASELINE_TABLE_PLACEHOLDER --- regenerated from "
        "results/multimodel_baseline.csv at paper-build time]\n" + bt + "\n"
    )
    paper = re.sub(
        r"% \[BASELINE_TABLE_PLACEHOLDER[^\]]*\][^\n]*\n(?:[^\n]*\\\\\s*\n)+\\midrule\n[^\n]*\\\\\s*\n",
        lambda m: bt_replacement,
        paper,
    )
    it_replacement = (
        "% [INTERVENTION_TABLE_PLACEHOLDER --- regenerated from "
        "results/intervention.csv at paper-build time]\n" + it + "\n"
    )
    paper = re.sub(
        r"% \[INTERVENTION_TABLE_PLACEHOLDER[^\]]*\][^\n]*\n(?:[^\n]*\\\\\s*\n)+",
        lambda m: it_replacement,
        paper,
    )
    PAPER.write_text(paper, encoding="utf-8")
    print(f"injected results into {PAPER}")
    print()
    print("--- Baseline table preview ---")
    print(bt)
    print()
    print("--- Intervention table preview ---")
    print(it)


if __name__ == "__main__":
    main()
