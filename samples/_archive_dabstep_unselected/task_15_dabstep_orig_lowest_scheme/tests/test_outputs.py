"""
Verifier for task_15_dabstep_orig_lowest_scheme: compound 'scheme:fee' answer.
"""
import os, re

RESULT_FILE = "/output/answer.txt"
SCHEME = "NexPay"
FEE_TRUTH = 0.140395
TOL = 0.001


def _read():
    assert os.path.exists(RESULT_FILE), f"Missing {RESULT_FILE}"
    with open(RESULT_FILE) as f:
        return re.sub(r"\s+", " ", f.read()).strip()


def test_file_exists():
    assert os.path.exists(RESULT_FILE)


def test_compound_match():
    pred = _read()
    parts = pred.split(":")
    assert len(parts) == 2, f"Expected 'scheme:fee' format, got {pred!r}"
    pred_scheme, pred_fee = parts[0].strip(), parts[1].strip()
    assert pred_scheme.lower() == SCHEME.lower(), (
        f"Scheme mismatch: predicted {pred_scheme!r}, expected {SCHEME!r}"
    )
    pred_fee_num = float(pred_fee.replace("EUR", "").strip())
    assert abs(pred_fee_num - FEE_TRUTH) <= TOL, (
        f"Fee mismatch: predicted {pred_fee_num}, expected {FEE_TRUTH} +/- {TOL}"
    )
