"""
Verifier for Task 6: design-adjusted linear regression coefficient of SBP
on age (controlling for male, BMI).

Ground truth (computed from clean NHANES Aug 2021 - Aug 2023 with WLS
point estimate + Taylor sandwich SE clustered on PSU within stratum):
  beta_age = 0.4026   SE = 0.0156   CI = (0.3720, 0.4332)

Tolerance:
  - beta_age within +/- 0.04 mm Hg/year of truth
  - se_age   within  [0.012, 0.025]  (rejects naive OLS SE ~0.005)
  - ci_lower within  [0.32, 0.41]
  - ci_upper within  [0.40, 0.49]
  - CI must bracket beta_age
"""
import json
import os

RESULT_FILE = "/output/result.json"
BETA_TRUTH = 0.4026
BETA_ABS_TOL = 0.04
SE_RANGE = (0.012, 0.025)
LOWER_RANGE = (0.32, 0.41)
UPPER_RANGE = (0.40, 0.49)


def _read():
    assert os.path.exists(RESULT_FILE), f"Missing {RESULT_FILE}"
    with open(RESULT_FILE) as f:
        return json.load(f)


def test_required_keys():
    d = _read()
    for k in ("beta_age", "se_age", "ci_lower", "ci_upper"):
        assert k in d, f"Missing key {k!r}"


def test_beta():
    b = float(_read()["beta_age"])
    assert abs(b - BETA_TRUTH) <= BETA_ABS_TOL, (
        f"beta_age={b}, expected {BETA_TRUTH} +/- {BETA_ABS_TOL}"
    )


def test_design_adjusted_se():
    se = float(_read()["se_age"])
    assert SE_RANGE[0] <= se <= SE_RANGE[1], (
        f"se_age={se} not in {SE_RANGE}; a value < 0.012 strongly suggests "
        "a naive (non-design-adjusted) SE."
    )


def test_ci_bounds():
    d = _read()
    lo, hi = float(d["ci_lower"]), float(d["ci_upper"])
    assert LOWER_RANGE[0] <= lo <= LOWER_RANGE[1], f"ci_lower {lo} not in {LOWER_RANGE}"
    assert UPPER_RANGE[0] <= hi <= UPPER_RANGE[1], f"ci_upper {hi} not in {UPPER_RANGE}"


def test_ci_brackets_beta():
    d = _read()
    lo, b, hi = float(d["ci_lower"]), float(d["beta_age"]), float(d["ci_upper"])
    assert lo < b < hi, f"CI must bracket beta_age ({lo} < {b} < {hi})"
