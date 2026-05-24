"""
Verifier for DABstep task 1871 (hard).

Ground truth (Adyen DABstep dev split, CC-BY-4.0):
  '-0.94810300000017'

Guidelines:
  'Answer must be just a number rounded to 14 decimals. If a question does not have a relevant or applicable answer for the...'
"""
import os
import re

RESULT_FILE = "/output/answer.txt"
GROUND_TRUTH = '-0.94810300000017'
ANSWER_MODE = 'number'      # "list" | "number" | "string"
NUM_TOL = 5e-14
NUM_DECIMALS = 14


def _normalise(s):
    return re.sub(r"\s+", " ", s).strip()


def _read_output():
    assert os.path.exists(RESULT_FILE), f"Missing {RESULT_FILE}"
    with open(RESULT_FILE, encoding="utf-8") as f:
        return _normalise(f.read())


def test_file_exists():
    assert os.path.exists(RESULT_FILE), f"Missing {RESULT_FILE}"


def test_answer_matches():
    pred = _read_output()
    if ANSWER_MODE == "number":
        try:
            pred_num = float(pred.replace(",", "").replace("EUR", "").strip())
            truth_num = float(str(GROUND_TRUTH).replace(",", "").strip())
        except ValueError as e:
            raise AssertionError(
                f"Expected a numeric answer; got {pred!r}. ({e})"
            )
        tol = NUM_TOL
        if tol is None:
            tol = abs(truth_num) * 1e-3 if truth_num else 1e-6
        assert abs(pred_num - truth_num) <= tol, (
            f"Predicted {pred_num}, expected {truth_num} +/- {tol:.6g}"
        )
    elif ANSWER_MODE == "list":
        # Normalise as set of trimmed tokens; case-insensitive
        def to_set(s):
            return set(t.strip().lower() for t in s.split(",") if t.strip())
        pred_set = to_set(pred)
        truth_set = to_set(str(GROUND_TRUTH))
        assert pred_set == truth_set, (
            f"List mismatch: extra={sorted(pred_set - truth_set)[:10]}, "
            f"missing={sorted(truth_set - pred_set)[:10]}, "
            f"|pred|={len(pred_set)}, |truth|={len(truth_set)}"
        )
    else:
        pred_n = pred.lower()
        truth_n = _normalise(str(GROUND_TRUTH)).lower()
        assert pred_n == truth_n, (
            f"Predicted {pred!r}, expected {GROUND_TRUTH!r}"
        )
