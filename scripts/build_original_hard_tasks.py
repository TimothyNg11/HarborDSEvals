"""Build 5 ORIGINAL hard tasks using the DABstep Adyen data + manual but
with brand-new questions whose ground truth I computed myself
(`scripts/dabstep_fee_engine.py`).

Each task ships the same /data/ bundle as the 10 DABstep tasks. The
questions are designed to fail gemini-3-flash-preview at pass@3:

  T11 — total Belles_cookbook_store 2023 fees (sum-all-matching-rules
        semantics), 4-decimal precision.
  T12 — counterfactual MCC change Belles 7997 -> 5411, fee delta,
        6-decimal precision.
  T13 — rank-5 merchant by 2023 total fees (very few merchants
        accrue any fee, ranking-edge case).
  T14 — sample SD (ddof=1) of monthly fees for Crossfit_Hanna across the
        12 months of 2023, 6-decimal precision.
  T15 — card scheme with the LOWEST average per-transaction 2023 fee,
        formatted as 'scheme:fee' with fee to 6 decimals.

Ground-truth answers (from oracle runs):
  T11: 3914.3621
  T12: +6177.500620
  T13: Belles_cookbook_store
  T14: 80.329334
  T15: NexPay:0.043202
"""
from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SAMPLES = ROOT / "samples"
CTX = ROOT / "_data_cache" / "DABstep" / "data" / "context"

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


def task_toml(task_id: str, slug: str, description: str, level: str = "hard") -> str:
    return f'''schema_version = "1.2"

artifacts = []

[task]
name = "abundant/dabstep-original-{task_id}-{slug}"
description = "Original DABstep-style hard task: {description}"
keywords = ["dabstep-original", "data-agent", "multi-step", "{level}"]

[[task.authors]]
name = "Abundant Research Eval"
email = "takehome@abundant.ai"

[metadata]
author_name = "Abundant Research Eval"
author_email = "takehome@abundant.ai"
difficulty = "{level}"
category = "data_science"
tags = ["dabstep-original", "implicit-rules", "multi-step-reasoning"]
expert_time_estimate_min = 60.0
junior_time_estimate_min = 240.0
source = "Original task; uses DABstep Adyen data (CC-BY-4.0)"

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


def make_task(name: str, instruction: str, answer: str, mode: str,
              num_tol: float | None, description: str, slug: str,
              task_id: str) -> None:
    tdir = SAMPLES / name
    if tdir.exists():
        shutil.rmtree(tdir)
    (tdir / "environment" / "data").mkdir(parents=True)
    (tdir / "solution").mkdir()
    (tdir / "tests").mkdir()

    for f in CTX.glob("*"):
        shutil.copy(f, tdir / "environment" / "data" / f.name)

    (tdir / "environment" / "Dockerfile").write_text(DOCKERFILE)
    (tdir / "instruction.md").write_text(instruction, encoding="utf-8")
    (tdir / "tests" / "test.sh").write_text(TEST_SH)
    (tdir / "task.toml").write_text(task_toml(task_id, slug, description),
                                    encoding="utf-8")

    # Oracle simply echoes the truth.
    safe = str(answer).replace("'", "'\\''")
    (tdir / "solution" / "solve.sh").write_text(
        f"#!/bin/bash\nset -e\ncat > /output/answer.txt <<'EOF'\n{safe}\nEOF\n"
        f"echo \"Oracle wrote: $(cat /output/answer.txt)\"\n"
    )

    # Verifier.
    if mode == "number":
        verifier = f'''"""
Verifier for {name}: numeric match within tolerance.
"""
import os, re

RESULT_FILE = "/output/answer.txt"
GROUND_TRUTH = {answer}
TOL = {num_tol if num_tol is not None else "1e-4"}


def _read():
    assert os.path.exists(RESULT_FILE), f"Missing {{RESULT_FILE}}"
    with open(RESULT_FILE) as f:
        return f.read().strip()


def test_file_exists():
    assert os.path.exists(RESULT_FILE)


def test_value_within_tolerance():
    raw = _read().replace(",", "").replace("EUR", "").replace("+", "").strip()
    pred = float(raw)
    truth = float(GROUND_TRUTH)
    assert abs(pred - truth) <= TOL, (
        f"Predicted {{pred}}, expected {{truth}} +/- {{TOL}}"
    )
'''
    elif mode == "string":
        verifier = f'''"""
Verifier for {name}: case-insensitive string match.
"""
import os, re

RESULT_FILE = "/output/answer.txt"
GROUND_TRUTH = {answer!r}


def _read():
    assert os.path.exists(RESULT_FILE), f"Missing {{RESULT_FILE}}"
    with open(RESULT_FILE) as f:
        return re.sub(r"\\s+", " ", f.read()).strip()


def test_file_exists():
    assert os.path.exists(RESULT_FILE)


def test_string_match():
    pred = _read().lower()
    truth = GROUND_TRUTH.strip().lower()
    assert pred == truth, f"Predicted {{pred!r}}, expected {{truth!r}}"
'''
    elif mode == "list":
        verifier = f'''"""
Verifier for {name}: comma-separated integer list, set-equality match.
"""
import os, re

RESULT_FILE = "/output/answer.txt"
GROUND_TRUTH = {answer!r}


def _read():
    assert os.path.exists(RESULT_FILE), f"Missing {{RESULT_FILE}}"
    with open(RESULT_FILE) as f:
        return f.read().strip()


def _to_set(s):
    return set(t.strip() for t in s.split(",") if t.strip())


def test_file_exists():
    assert os.path.exists(RESULT_FILE)


def test_set_equality():
    pred_set = _to_set(_read())
    truth_set = _to_set(GROUND_TRUTH)
    extra = sorted(pred_set - truth_set)
    missing = sorted(truth_set - pred_set)
    assert pred_set == truth_set, (
        f"List mismatch: extra={{extra[:10]}}, missing={{missing[:10]}}, "
        f"|pred|={{len(pred_set)}}, |truth|={{len(truth_set)}}"
    )
'''
    elif mode == "compound":
        # "scheme:fee" — split on colon, scheme must match, fee within tol
        scheme, fee = str(answer).split(":")
        verifier = f'''"""
Verifier for {name}: compound 'scheme:fee' answer.
"""
import os, re

RESULT_FILE = "/output/answer.txt"
SCHEME = "{scheme}"
FEE_TRUTH = {fee}
TOL = {num_tol if num_tol is not None else "5e-6"}


def _read():
    assert os.path.exists(RESULT_FILE), f"Missing {{RESULT_FILE}}"
    with open(RESULT_FILE) as f:
        return re.sub(r"\\s+", " ", f.read()).strip()


def test_file_exists():
    assert os.path.exists(RESULT_FILE)


def test_compound_match():
    pred = _read()
    parts = pred.split(":")
    assert len(parts) == 2, f"Expected 'scheme:fee' format, got {{pred!r}}"
    pred_scheme, pred_fee = parts[0].strip(), parts[1].strip()
    assert pred_scheme.lower() == SCHEME.lower(), (
        f"Scheme mismatch: predicted {{pred_scheme!r}}, expected {{SCHEME!r}}"
    )
    pred_fee_num = float(pred_fee.replace("EUR", "").strip())
    assert abs(pred_fee_num - FEE_TRUTH) <= TOL, (
        f"Fee mismatch: predicted {{pred_fee_num}}, expected {{FEE_TRUTH}} +/- {{TOL}}"
    )
'''
    else:
        raise ValueError(mode)

    (tdir / "tests" / "test_outputs.py").write_text(verifier, encoding="utf-8")
    print(f"built {name}  mode={mode}  truth={answer!r}")


def main():
    # ------ Task 11
    make_task(
        name="task_11_dabstep_orig_belles_total_2023",
        slug="belles-total",
        task_id="11",
        description="Belles_cookbook_store 2023 total fees (sum-all-matching-rules), 4 decimals",
        instruction=r"""# Total fees paid by Belles_cookbook_store in 2023

This task uses the DABstep payment-processing dataset and manual in `/data/`.
The fee-matching semantics is the standard one described in section 5 of
`/data/manual.md`: a rule applies to a transaction iff every non-null rule
field matches the transaction (empty list / null is "any").

For each transaction, the fee charged is the **sum** of
`fixed_amount + rate * eur_amount / 10000` across **every** matching fee
rule. (Some hard DABstep tasks use exactly this semantics, e.g. the
dev-split list-of-applicable-fee-IDs questions.)

## Question

What is the total fees (in EUR) that Belles_cookbook_store paid across
**all of 2023**, summed across every matching fee rule per transaction?

## Required output

Write a single non-negative number, rounded to **4 decimal places**, to
`/output/answer.txt`. Example format: `3914.3621`

## Notes

- The environment has no internet access.
- All data live in `/data/`: `payments.csv`, `fees.json`,
  `merchant_data.json`, `merchant_category_codes.csv`,
  `acquirer_countries.csv`, `manual.md`, `payments-readme.md`.
- Belles_cookbook_store has 13,848 transactions in 2023; expect non-trivial
  computation.
""",
        answer="3914.3621",
        mode="number",
        num_tol=0.001,
    )

    # ------ Task 12 — counterfactual MCC change
    make_task(
        name="task_12_dabstep_orig_belles_mcc_counterfactual",
        slug="mcc-counterfactual",
        task_id="12",
        description="Counterfactual MCC change Belles 7997->5411, fee delta, 6 decimals",
        instruction=r"""# Counterfactual fee delta when Belles_cookbook_store reclassifies MCC

This task uses the DABstep payment-processing dataset and manual in `/data/`.
The fee-matching semantics is the standard one in section 5 of
`/data/manual.md`: a rule applies iff every non-null field matches; the fee
per transaction is the **sum** across every matching rule.

Belles_cookbook_store currently has `merchant_category_code = 7997`
(per `/data/merchant_data.json`). Suppose Belles reclassifies its MCC to
`5411` (Grocery Stores, Supermarkets), keeping every other merchant
attribute unchanged.

## Question

What is the resulting **delta in total 2023 fees** (new total minus old
total), in EUR? A positive number means Belles pays MORE under the new
MCC; negative means LESS.

## Required output

Write a single signed number, rounded to **6 decimal places**, to
`/output/answer.txt`. Example format: `+6177.500620` or `-1234.567890`
(the leading sign is optional for positive numbers).

## Notes

- The environment has no internet access.
- All data live in `/data/`. The merchant file shows current MCC; for
  this task, mutate Belles's MCC only.
- The same fee-rule-matching code that computes the original-MCC total
  fees can be re-run with `5411` swapped in.
""",
        answer="+6177.500620",
        mode="number",
        num_tol=0.00001,
    )

    # ------ Task 13 — list of applicable fee_ids across 5 fee-accruing merchants
    make_task(
        name="task_13_dabstep_orig_fee_ids_nonzero_merchants",
        slug="fee-ids-nonzero",
        task_id="13",
        description="All fee IDs applicable to any 2023 transaction of the 5 fee-accruing merchants, sorted",
        instruction=r"""# All fee IDs applicable to fee-accruing merchants in 2023

This task uses the DABstep payment-processing dataset and manual in
`/data/`. The fee-matching semantics is the standard one in section 5 of
`/data/manual.md`: a rule applies to a transaction iff every non-null
rule field matches the transaction (empty list / null is "any").

Five of the 30 merchants in `/data/merchant_data.json` accrue any fees
at all across 2023 — the rest match zero rules and pay nothing. The five
fee-accruing merchants are:

- Crossfit_Hanna
- Martinis_Fine_Steakhouse
- Belles_cookbook_store
- Golfclub_Baron_Friso
- Rafa_AI

## Question

Compute the **set of all fee_ids** that apply to at least one
transaction in 2023 across these five merchants (union of applicable
rule IDs over their 2023 transactions). Output the sorted ascending list.

## Required output

Write a single line to `/output/answer.txt` with the fee IDs in ascending
order, comma-separated, no spaces. Example format:
`12,16,29,36,38,51,64,...`

## Notes

- The environment has no internet access.
- The set has many dozens of IDs; the verifier compares as a set of
  integers (order doesn't matter for matching but extra/missing IDs both
  fail).
- A common pitfall is to apply a "most-specific match" interpretation
  instead of the manual's "every matching rule applies" semantics.
""",
        answer="12,16,29,36,38,51,64,65,79,84,89,107,123,134,150,162,163,183,187,217,231,276,280,284,286,300,304,332,347,364,367,381,384,428,431,433,456,473,477,491,498,501,536,547,556,572,595,612,616,622,626,631,637,640,648,660,678,680,682,701,702,704,709,721,741,769,787,792,804,813,834,849,858,861,863,870,871,878,884,888,891,892,913,915,921,980,996",
        mode="list",
        num_tol=None,
    )

    # ------ Task 14 — Crossfit_Hanna monthly fee SD
    make_task(
        name="task_14_dabstep_orig_crossfit_monthly_sd",
        slug="crossfit-monthly-sd",
        task_id="14",
        description="Sample SD (ddof=1) of monthly Crossfit_Hanna fees 2023, 6 decimals",
        instruction=r"""# Standard deviation of Crossfit_Hanna's monthly fees in 2023

This task uses the DABstep payment-processing dataset and manual in `/data/`.
The fee-matching semantics is the standard one in section 5 of
`/data/manual.md`: a rule applies iff every non-null field matches; the fee
per transaction is the **sum** across every matching rule.

For Crossfit_Hanna in 2023, compute the **per-transaction fee** for every
one of their transactions, group those fees by **calendar month** (using
`day_of_year` mapped to a 2023 calendar — i.e. day 1 = Jan 1, day 32 =
Feb 1, accounting for the fact that 2023 is not a leap year), sum within
each month to get a series of 12 monthly totals, then compute the
**sample standard deviation** of those 12 monthly totals with the
Bessel-corrected denominator `n - 1` (ddof = 1).

## Question

What is the sample standard deviation (ddof = 1) of Crossfit_Hanna's
12 monthly fee totals for 2023, in EUR?

## Required output

Write a single non-negative number, rounded to **6 decimal places**, to
`/output/answer.txt`. Example format: `80.329334`

## Notes

- The environment has no internet access.
- Use the population-of-12 (Jan–Dec 2023) and sample SD (ddof = 1). The
  population SD (ddof = 0) differs and will fail the verifier.
- The fee for a transaction is the sum across every matching rule.
""",
        answer="80.329334",
        mode="number",
        num_tol=0.0001,
    )

    # ------ Task 15 — lowest avg fee card scheme
    make_task(
        name="task_15_dabstep_orig_lowest_scheme",
        slug="lowest-scheme",
        task_id="15",
        description="Card scheme with the lowest average per-transaction fee in 2023, 'scheme:fee'",
        instruction=r"""# Card scheme with the lowest average per-transaction fee

This task uses the DABstep payment-processing dataset and manual in `/data/`.
The fee-matching semantics is the standard one in section 5 of
`/data/manual.md`: a rule applies iff every non-null field matches; the fee
per transaction is the **sum** across every matching rule.

Compute the **average per-transaction fee** (in EUR) for each card scheme
present in `payments.csv` (GlobalCard, NexPay, SwiftCharge, TransactPlus)
across **all 2023 transactions**.

## Question

Which card scheme has the LOWEST average per-transaction fee, and what
is that average?

## Required output

Write your answer to `/output/answer.txt` in the format
`scheme_name:average_fee` where `average_fee` is rounded to 6 decimal
places. Example format: `NexPay:0.043202`. No extra prose; no trailing
units.

## Notes

- The environment has no internet access.
- Per-transaction fee = sum across every matching rule (a transaction
  may match many rules; many transactions match zero rules and contribute
  a fee of 0 EUR).
- The average is over all transactions for that scheme (including
  zero-fee transactions).
""",
        answer="NexPay:0.043202",
        mode="compound",
        num_tol=5e-6,
    )

    print("\nAll 5 original tasks built.")


if __name__ == "__main__":
    main()
