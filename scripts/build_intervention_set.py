"""Build samples_intervention/ from 5 baseline tasks.

For each of T05–T09, copy the task directory into samples_intervention/ and
prepend a single explicit rule-semantics block to instruction.md. Every other
file (verifier, task.toml, solution, environment) is byte-identical to the
baseline, so any pass@3 delta between samples/ and samples_intervention/
attributes cleanly to the prompt change.
"""
from __future__ import annotations

import shutil
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "samples"
DST = ROOT / "samples_intervention"

TARGETS = [
    "task_05_dabstep_1305_for-account-type-h-and",
    "task_06_dabstep_1464_what-is-the-fee-id",
    "task_07_dabstep_1681_for-the-th-of-the",
    "task_08_dabstep_1753_what-are-the-applicable-fee",
    "task_09_dabstep_1871_in-january-what-delta-would",
]

INTERVENTION_BLOCK = textwrap.dedent("""\
    > **Important rule-matching semantics for fee rules in `/data/fees.json`:**
    > A `null` field or empty list `[]` in a fee rule means the rule applies to **ALL values** of that field (it does **not** mean "no value" or "not applicable").
    > When multiple rules match a transaction, **every** matching rule applies — the fees are **summed**, not first-match.

    """)


def main():
    DST.mkdir(exist_ok=True)
    built = 0
    for name in TARGETS:
        src = SRC / name
        dst = DST / name
        if not src.exists():
            print(f"WARN: source missing: {src}")
            continue
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
        inst_path = dst / "instruction.md"
        original = inst_path.read_text(encoding="utf-8")
        inst_path.write_text(INTERVENTION_BLOCK + original, encoding="utf-8")
        print(f"built {name}")
        built += 1
    print(f"\nDone — built {built} intervention task variants in {DST}.")

    # Also persist the verbatim block for results/intervention_prompt.diff
    results_dir = ROOT / "results"
    results_dir.mkdir(exist_ok=True)
    (results_dir / "intervention_prompt.diff").write_text(
        "# Verbatim block prepended to instruction.md in samples_intervention/.\n"
        "# This is the ONLY difference between baseline and intervention task variants.\n"
        "\n"
        + INTERVENTION_BLOCK,
        encoding="utf-8",
    )
    print(f"wrote {results_dir / 'intervention_prompt.diff'}")


if __name__ == "__main__":
    main()
