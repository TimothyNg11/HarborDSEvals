"""Build 15 additional Harbor tasks from the DABstep default split.

Extends the existing 10-task set (built by build_dabstep_tasks.py) to 25
tasks total. Task IDs were selected from the DABstep hard split to maximise
failure-mode coverage across:

  - Rule-precedence misread (null/empty = any):   1696, 1763, 1502, 1700, 1470
  - Multi-filter avg-fee (like T05):              1427, 1348
  - 14-decimal counterfactual delta (like T09):   2520, 2480, 2484
  - ACI combinatorial optimisation (like T10):    2769, 2746, 2729, 2767
  - Combinatorial card-scheme optimisation:       2691

Existing task directories (task_01 – task_10) are never touched; this script
only creates task_11 – task_25.
"""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from datasets import load_dataset

ROOT = Path(__file__).resolve().parent.parent
SAMPLES = ROOT / "samples"
DABSTEP_CTX = ROOT / "_data_cache" / "DABstep" / "data" / "context"

# Task IDs to build, in the order they should be numbered (task_11 … task_25).
TARGET_TASK_IDS = [
    1696,   # fee IDs Golfclub day 200      — null/any + monthly buckets
    1763,   # fee IDs Crossfit_Hanna Jan    — null/any, different merchant
    1502,   # fee IDs acct_type O + aci E   — direct T06 analogue
    1700,   # fee IDs Martinis day 12       — null/any + bucket
    1470,   # fee IDs acct_type D + aci A   — null/any like T06
    1427,   # avg fee acct_type H, Taxicabs — multi-filter like T05
    1348,   # avg fee acct_type H, Drinking Places — multi-filter
    2520,   # Rafa_AI delta fee 276 rate    — 14-decimal counterfactual
    2480,   # Belles delta fee rate         — 14-decimal counterfactual
    2484,   # Crossfit_Hanna delta          — 14-decimal counterfactual
    2769,   # Golfclub ACI optimise 2023    — combinatorial like T10
    2746,   # Rafa_AI ACI optimise October  — combinatorial
    2729,   # Golfclub ACI optimise July    — combinatorial
    2767,   # Belles ACI optimise           — combinatorial
    2691,   # cheapest card scheme December — combinatorial + monthly
]
START_IDX = 11   # first task number to assign (task_11, task_12, …)

# ---------- templates (identical to build_dabstep_tasks.py) ----------

DOCKERFILE = """FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \\
        ca-certificates \\
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \\
        pandas==2.2.2 \\
        numpy==1.26.4 \\
        scipy==1.13.1 \\
        statsmodels==0.14.2 \\
        openpyxl==3.1.5 \\
        pytest==8.4.1 \\
        pytest-json-ctrf==0.3.5

WORKDIR /app
COPY data /data
RUN mkdir -p /output && chmod 777 /output

CMD ["/bin/bash"]
"""

TEST_SH = """#!/bin/bash
set -u
mkdir -p /logs/verifier
pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA
rc=$?
if [ $rc -eq 0 ]; then
    echo 1 > /logs/verifier/reward.txt
else
    echo 0 > /logs/verifier/reward.txt
fi
exit 0
"""

INSTRUCTION_TEMPLATE = """# DABstep task {task_id} ({level})

> Adapted from the DABstep default split (Adyen, CC-BY-4.0;
> arXiv:2506.23719). The full set of context files is in `/data/`.

## Question

{question}

## Answer guidelines

{guidelines}

## Required output

Write your final answer to `/output/answer.txt` as a single line of plain
text following the guidelines above. Trailing whitespace / newline are
stripped before comparison; capitalisation of pure-text answers is ignored
when the guidelines do not specify otherwise.

## Available files

- `/data/payments.csv`                — payment transactions (138k rows)
- `/data/payments-readme.md`          — schema for payments.csv
- `/data/merchant_data.json`          — merchant attributes (account_type,
                                         MCC, capture_delay, etc.)
- `/data/merchant_category_codes.csv` — MCC → description lookup
- `/data/fees.json`                   — fee rules keyed on attributes
                                         described in the manual
- `/data/acquirer_countries.csv`      — acquirer-country lookup
- `/data/manual.md`                   — merchant guide ("Optimizing Payment
                                         Processing and Minimizing Fees");
                                         contains the implicit rules you
                                         will need

## Notes

- The environment has no internet access; everything you need is in `/data/`.
- The DABstep manual describes how fee rules combine across MCC, acquirer
  country, account type, ACI, and transaction-level signals. Many questions
  hinge on rules that are NOT spelled out in a single formula — they have to
  be inferred from rule precedence and matching semantics described in the
  manual.
- Answers must follow the guidelines format EXACTLY. The verifier compares
  after light normalisation (trim, lower-case for pure-text answers, sort
  comma-separated lists). Stray prose around the answer will fail.
"""

VERIFIER_TEMPLATE = '''"""
Verifier for DABstep task {task_id} ({level}).

Ground truth (Adyen DABstep default split, CC-BY-4.0):
  {answer_truth!r}

Guidelines:
  {guidelines_short!r}
"""
import os
import re

RESULT_FILE = "/output/answer.txt"
GROUND_TRUTH = {answer_truth!r}
ANSWER_MODE = {mode!r}      # "list" | "number" | "string"
NUM_TOL = {num_tol}
NUM_DECIMALS = {num_decimals}


def _normalise(s):
    return re.sub(r"\\s+", " ", s).strip()


def _read_output():
    assert os.path.exists(RESULT_FILE), f"Missing {{RESULT_FILE}}"
    with open(RESULT_FILE, encoding="utf-8") as f:
        return _normalise(f.read())


def test_file_exists():
    assert os.path.exists(RESULT_FILE), f"Missing {{RESULT_FILE}}"


def test_answer_matches():
    pred = _read_output()
    if ANSWER_MODE == "number":
        try:
            pred_num = float(pred.replace(",", "").replace("EUR", "").strip())
            truth_num = float(str(GROUND_TRUTH).replace(",", "").strip())
        except ValueError as e:
            raise AssertionError(
                f"Expected a numeric answer; got {{pred!r}}. ({{e}})"
            )
        tol = NUM_TOL
        if tol is None:
            tol = abs(truth_num) * 1e-3 if truth_num else 1e-6
        assert abs(pred_num - truth_num) <= tol, (
            f"Predicted {{pred_num}}, expected {{truth_num}} +/- {{tol:.6g}}"
        )
    elif ANSWER_MODE == "list":
        def to_set(s):
            return set(t.strip().lower() for t in s.split(",") if t.strip())
        pred_set = to_set(pred)
        truth_set = to_set(str(GROUND_TRUTH))
        assert pred_set == truth_set, (
            f"List mismatch: extra={{sorted(pred_set - truth_set)[:10]}}, "
            f"missing={{sorted(truth_set - pred_set)[:10]}}, "
            f"|pred|={{len(pred_set)}}, |truth|={{len(truth_set)}}"
        )
    else:
        pred_n = pred.lower()
        truth_n = _normalise(str(GROUND_TRUTH)).lower()
        assert pred_n == truth_n, (
            f"Predicted {{pred!r}}, expected {{GROUND_TRUTH!r}}"
        )
'''

SOLVE_SH_TEMPLATE = """#!/bin/bash
# Oracle: write the published DABstep answer to /output/answer.txt.
set -e
cat > /output/answer.txt <<'EOF'
{answer_text}
EOF
echo "Oracle wrote answer: $(cat /output/answer.txt | head -c 80)..."
"""

TASK_TOML_TEMPLATE = '''schema_version = "1.2"

artifacts = []

[task]
name = "abundant/dabstep-task-{task_id}-{slug}"
description = "DABstep task {task_id} ({level}) - {short_desc}"
keywords = ["dabstep", "data-agent", "multi-step", "{level}"]

[[task.authors]]
name = "Abundant Research Eval"
email = "takehome@abundant.ai"

[metadata]
author_name = "Abundant Research Eval"
author_email = "takehome@abundant.ai"
difficulty = "{level}"
category = "data_science"
tags = ["dabstep", "multi-step-reasoning", "implicit-rules"]
expert_time_estimate_min = {expert_min}
junior_time_estimate_min = {junior_min}
source = "DABstep (arXiv:2506.23719) default split, Adyen CC-BY-4.0"
source_task_id = "{task_id}"
difficulty_level = "{level}"

[verifier]
timeout_sec = 120.0

[verifier.env]

[agent]
timeout_sec = 1800.0

[environment]
build_timeout_sec = 600.0
os = "linux"
cpus = 2
memory_mb = 4096
storage_mb = 8192
gpus = 0
allow_internet = true
mcp_servers = []

[environment.env]

[solution.env]
'''


def detect_answer_mode(guidelines: str, answer: str) -> tuple[str, float | None, int | None]:
    g = guidelines.lower()
    if "comma separated list" in g or "list of values" in g:
        return ("list", None, None)
    if "number" in g and "rounded" in g:
        match = re.search(r"rounded to (\d+) decimals?", g)
        decimals = int(match.group(1)) if match else 2
        tol = 10 ** (-decimals) * 5
        return ("number", tol, decimals)
    if "number" in g:
        return ("number", None, None)
    return ("string", None, None)


def slugify(text: str, n: int = 5) -> str:
    words = re.findall(r"[A-Za-z]+", text.lower())[:n]
    return "-".join(words) or "task"


def main():
    ds = load_dataset("adyen/DABstep", name="tasks", split="default",
                      cache_dir=str(ROOT / "_data_cache" / "DABstep_hf"))

    # Index the full split by task_id for fast lookup (task_ids are strings)
    by_id = {t["task_id"]: t for t in ds}

    built = 0
    for offset, task_id in enumerate(TARGET_TASK_IDS):
        task = by_id.get(str(task_id))
        if task is None:
            print(f"WARN: task_id={task_id} not found in default split — skipping")
            continue

        idx = START_IDX + offset   # task_11, task_12, …
        question  = task["question"]
        answer    = task["answer"]
        guidelines = task["guidelines"]
        level     = task["level"]

        mode, num_tol, num_decimals = detect_answer_mode(guidelines, answer)
        slug = slugify(question, n=5)
        task_dir_name = f"task_{idx:02d}_dabstep_{task_id}_{slug}"[:80]
        task_dir = SAMPLES / task_dir_name

        if task_dir.exists():
            print(f"skip  {task_dir.name}  (already exists)")
            continue

        (task_dir / "environment" / "data").mkdir(parents=True)
        (task_dir / "solution").mkdir()
        (task_dir / "tests").mkdir()

        for f in DABSTEP_CTX.glob("*"):
            shutil.copy(f, task_dir / "environment" / "data" / f.name)

        (task_dir / "instruction.md").write_text(
            INSTRUCTION_TEMPLATE.format(
                task_id=task_id, level=level,
                question=question, guidelines=guidelines,
            ),
            encoding="utf-8",
        )
        (task_dir / "environment" / "Dockerfile").write_text(DOCKERFILE)
        (task_dir / "tests" / "test.sh").write_text(TEST_SH)

        guidelines_short = (guidelines[:120] + "...") if len(guidelines) > 120 else guidelines
        (task_dir / "tests" / "test_outputs.py").write_text(
            VERIFIER_TEMPLATE.format(
                task_id=task_id, level=level,
                answer_truth=answer, guidelines_short=guidelines_short,
                mode=mode,
                num_tol=num_tol if num_tol is not None else "None",
                num_decimals=num_decimals if num_decimals is not None else "None",
            ),
            encoding="utf-8",
        )

        ans_text = str(answer).replace("'", "'\\''")
        (task_dir / "solution" / "solve.sh").write_text(
            SOLVE_SH_TEMPLATE.format(answer_text=ans_text),
            encoding="utf-8",
        )

        expert_min = 20 if level == "easy" else 60
        junior_min = 60 if level == "easy" else 180
        short_desc = question[:60].replace("'", "'")
        (task_dir / "task.toml").write_text(
            TASK_TOML_TEMPLATE.format(
                task_id=task_id, slug=slug, level=level,
                short_desc=short_desc, expert_min=expert_min,
                junior_min=junior_min,
            ),
            encoding="utf-8",
        )

        print(f"built {task_dir.name}  (level={level}, mode={mode}, answer={str(answer)[:40]})")
        built += 1

    print(f"\nDone — built {built} new tasks. Active set now has "
          f"{len(list(SAMPLES.glob('task_*')))} tasks.")


if __name__ == "__main__":
    main()
