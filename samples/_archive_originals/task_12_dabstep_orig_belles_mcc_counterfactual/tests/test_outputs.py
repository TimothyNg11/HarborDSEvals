"""
Verifier for task_12_dabstep_orig_belles_mcc_counterfactual: numeric match within tolerance.
"""
import os, re

RESULT_FILE = "/output/answer.txt"
GROUND_TRUTH = +6690.646000
TOL = 0.001


def _read():
    assert os.path.exists(RESULT_FILE), f"Missing {RESULT_FILE}"
    with open(RESULT_FILE) as f:
        return f.read().strip()


def test_file_exists():
    assert os.path.exists(RESULT_FILE)


def test_value_within_tolerance():
    raw = _read().replace(",", "").replace("EUR", "").replace("+", "").strip()
    pred = float(raw)
    truth = float(GROUND_TRUTH)
    assert abs(pred - truth) <= TOL, (
        f"Predicted {pred}, expected {truth} +/- {TOL}"
    )
