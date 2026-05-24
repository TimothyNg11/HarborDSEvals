"""
Verifier for Task 10: Erreygers concentration index of SEVERE obesity
(BMI >= 40) over family income-to-poverty ratio.

Ground truth (computed from messy NHANES data with WTMEC2YR + p_pir_ratio
filter):
  standard C        = -0.1210
  Erreygers E       = -0.0420
  mu_y (prev sev.)  =  0.0961
  correction factor =  0.3474

The Erreygers and standard indices differ by ~0.079 here, so reporting
the standard C (-0.121) will land WELL outside the tolerance band on E.

Tolerance: +/- 0.020 absolute on the Erreygers index. The verifier also
explicitly rejects:
  - values near 0 (no inequality),
  - the standard-C value (-0.12) by being out of band,
  - a wrong-sign positive value (means income ranking inverted).
"""
import os

RESULT_FILE = "/output/result.txt"
GROUND_TRUTH = -0.0420
ABS_TOL = 0.020


def test_file_exists():
    assert os.path.exists(RESULT_FILE), f"Missing {RESULT_FILE}"


def test_parses_as_number():
    with open(RESULT_FILE) as f:
        raw = f.read().strip().replace(",", "")
    float(raw)


def test_value_within_tolerance():
    with open(RESULT_FILE) as f:
        v = float(f.read().strip().replace(",", ""))
    lo, hi = GROUND_TRUTH - ABS_TOL, GROUND_TRUTH + ABS_TOL
    assert lo <= v <= hi, (
        f"Predicted {v}, expected {GROUND_TRUTH} +/- {ABS_TOL} "
        f"(range [{lo:.4f}, {hi:.4f}])"
    )


def test_sign_is_negative():
    with open(RESULT_FILE) as f:
        v = float(f.read().strip().replace(",", ""))
    assert v < 0, (
        f"Predicted {v}; severe obesity concentrates among lower-income "
        "households, so E < 0. Positive sign indicates inverted income "
        "ranking."
    )


def test_not_standard_index():
    # The standard (Wagstaff) C for the same data is roughly -0.12, which
    # is FAR outside the Erreygers tolerance band. If the agent submitted
    # the standard index, this catches it cleanly.
    with open(RESULT_FILE) as f:
        v = float(f.read().strip().replace(",", ""))
    assert v > -0.08, (
        f"Predicted {v}; this is in the range of the *standard* Wagstaff "
        "concentration index, not the Erreygers index. The Erreygers "
        "index for this outcome is roughly 0.35 x the standard index."
    )
