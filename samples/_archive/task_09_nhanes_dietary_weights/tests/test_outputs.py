"""
Verifier for Task 9: weighted MAD around the weighted median of sodium
intake (mg) among adult women.

Ground truth (computed from messy NHANES DR1TOT_L using WTDRD1 +
DR1DRSTZ=1, with linear-interp weighted quantile, applied twice):
  weighted median sodium = 2551.7 mg
  weighted MAD = 765.3 mg

Tolerance: +/- 60 mg absolute on the wMAD.

Most likely wrong answers:
  - scipy.stats.median_abs_deviation (unweighted) ~ 761 mg (would pass
    here, since the distribution is nearly symmetric in this slice).
  - Using exam weight WTMEC2YR instead of WTDRD1 ~ 770-790 mg
    (typically still within tolerance).
  - Using the standard deviation: ~ 1300+ mg (clearly out of band).
  - Using the variance: ~ 1.6e6 (orders of magnitude off).
  - Using the IQR: ~ 1600 mg (clearly out of band).
"""
import os

RESULT_FILE = "/output/result.txt"
GROUND_TRUTH = 765.3
ABS_TOL = 60.0


def test_file_exists():
    assert os.path.exists(RESULT_FILE), f"Missing {RESULT_FILE}"


def test_parses_as_number():
    with open(RESULT_FILE) as f:
        raw = f.read().strip().replace(",", "").replace("mg", "")
    float(raw)


def test_value_within_tolerance():
    with open(RESULT_FILE) as f:
        v = float(f.read().strip().replace(",", "").replace("mg", ""))
    lo, hi = GROUND_TRUTH - ABS_TOL, GROUND_TRUTH + ABS_TOL
    assert lo <= v <= hi, (
        f"Predicted {v} mg, expected {GROUND_TRUTH} +/- {ABS_TOL} "
        f"(range [{lo:.1f}, {hi:.1f}])"
    )


def test_not_iqr_or_sd():
    # Reject answers that are clearly the wrong statistic.
    with open(RESULT_FILE) as f:
        v = float(f.read().strip().replace(",", "").replace("mg", ""))
    assert v < 1100, (
        f"Predicted {v} mg; looks like the IQR (~1600), SD (~1300), or "
        "variance, not the wMAD (~765)."
    )
    assert v > 200, (
        f"Predicted {v} mg; too small for a dispersion measure of sodium "
        "(individual intakes vary in the thousands of mg)."
    )
