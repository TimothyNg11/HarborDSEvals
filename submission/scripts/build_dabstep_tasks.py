"""Build 10 Harbor tasks from the DABstep dev split.

Each task wraps a single DABstep dev-split question:
 - instruction.md: question + guidelines verbatim
 - environment/data/: full DABstep context (manual.md, payments.csv, fees.json,
   merchant_data.json, merchant_category_codes.csv, acquirer_countries.csv,
   payments-readme.md)
 - solution/solve.sh: writes the published answer to /output/answer.txt
 - tests/test_outputs.py: string-match verifier (case-insensitive, normalized)
 - tests/test.sh: pytest entrypoint
 - environment/Dockerfile: python:3.11-slim + pandas + pytest

Ground-truth answers come from the official DABstep dev split released under
CC-BY-4.0 by Adyen (huggingface.co/datasets/adyen/DABstep). Cite in report.
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
SAMPLES.mkdir(exist_ok=True)


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

> Adapted from the DABstep dev split (Adyen, CC-BY-4.0;
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

- The environment has no internet access; everything you need is in
  `/data/`.
- The DABstep manual describes how fee rules combine across MCC, acquirer
  country, account type, ACI, and transaction-level signals. Many
  questions hinge on rules that are NOT spelled out in a single formula —
  they have to be inferred from rule precedence and matching semantics
  described in the manual.
- Answers must follow the guidelines format EXACTLY. The verifier compares
  after light normalisation (trim, lower-case for pure-text answers, sort
  comma-separated lists). Stray prose around the answer will fail.
"""

VERIFIER_TEMPLATE = '''"""
Verifier for DABstep task {task_id} ({level}).

Ground truth (Adyen DABstep dev split, CC-BY-4.0):
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
        # Normalise as set of trimmed tokens; case-insensitive
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
# Oracle: write the published DABstep dev-split answer to /output/answer.txt.
# Ground truth is supplied as a constant (the model has no access to this
# file when run as gemini-cli).
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
description = "DABstep dev-split task {task_id} ({level}) - {short_desc}"
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
source = "DABstep (arXiv:2506.23719) dev split, Adyen CC-BY-4.0"
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
    """Return (mode, num_tol, num_decimals)."""
    g = guidelines.lower()
    a = str(answer).strip()
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


def slugify(text: str, n: int = 4) -> str:
    words = re.findall(r"[A-Za-z]+", text.lower())[:n]
    return "-".join(words) or "task"


def main():
    ds = load_dataset("adyen/DABstep", name="tasks", split="dev",
                      cache_dir=str(ROOT / "_data_cache" / "DABstep_hf"))

    for idx, task in enumerate(ds, 1):
        task_id = task["task_id"]
        question = task["question"]
        answer = task["answer"]
        guidelines = task["guidelines"]
        level = task["level"]

        mode, num_tol, num_decimals = detect_answer_mode(guidelines, answer)
        slug = slugify(question, n=5)
        task_dir_name = f"task_{idx:02d}_dabstep_{task_id}_{slug}"[:80]
        task_dir = SAMPLES / task_dir_name
        if task_dir.exists():
            shutil.rmtree(task_dir)
        (task_dir / "environment" / "data").mkdir(parents=True)
        (task_dir / "solution").mkdir()
        (task_dir / "tests").mkdir()

        # Copy all context files
        for f in DABSTEP_CTX.glob("*"):
            shutil.copy(f, task_dir / "environment" / "data" / f.name)

        # instruction.md
        (task_dir / "instruction.md").write_text(
            INSTRUCTION_TEMPLATE.format(
                task_id=task_id,
                level=level,
                question=question,
                guidelines=guidelines,
            ),
            encoding="utf-8",
        )

        # Dockerfile
        (task_dir / "environment" / "Dockerfile").write_text(DOCKERFILE)

        # test.sh
        (task_dir / "tests" / "test.sh").write_text(TEST_SH)

        # test_outputs.py
        guidelines_short = (guidelines[:120] + "...") if len(guidelines) > 120 else guidelines
        verifier_text = VERIFIER_TEMPLATE.format(
            task_id=task_id,
            level=level,
            answer_truth=answer,
            guidelines_short=guidelines_short,
            mode=mode,
            num_tol=num_tol if num_tol is not None else "None",
            num_decimals=num_decimals if num_decimals is not None else "None",
        )
        (task_dir / "tests" / "test_outputs.py").write_text(verifier_text, encoding="utf-8")

        # solve.sh — embed the answer verbatim
        # If answer contains EOF, escape; otherwise embed directly.
        ans_text = str(answer).replace("'", "'\\''")  # safe for here-doc
        (task_dir / "solution" / "solve.sh").write_text(
            SOLVE_SH_TEMPLATE.format(answer_text=ans_text),
            encoding="utf-8",
        )

        # task.toml
        expert_min = 20 if level == "easy" else 60
        junior_min = 60 if level == "easy" else 180
        short_desc = question[:60].replace("'", "’")
        (task_dir / "task.toml").write_text(
            TASK_TOML_TEMPLATE.format(
                task_id=task_id,
                slug=slug,
                level=level,
                short_desc=short_desc,
                expert_min=expert_min,
                junior_min=junior_min,
            ),
            encoding="utf-8",
        )

        print(f"built {task_dir.name}  (level={level}, mode={mode})")

    print("\nDone")


if __name__ == "__main__":
    main()
