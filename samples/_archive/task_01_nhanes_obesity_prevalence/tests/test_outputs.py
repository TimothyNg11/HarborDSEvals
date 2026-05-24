"""
Verifier for Task 1: prevalence + Wilson CI for a 4-condition compound
subgroup.

The subgroup (non-Hispanic Asian women age 50-69 born outside the US) is
small enough that the design-effective sample size is on the order of 20.
The Wilson-on-effective-n CI is the only CI that survives at this n; a
symmetric Wald CI or a naive binomial CI will be visibly off.

Ground truth (computed from the messy NHANES extract):
  point  ≈ 8.1 %  (varies slightly with cleaning details)
  CI lower ≈ 1.5 %
  CI upper ≈ 34.7 %

Tolerance:
  - point within +/- 5 pp absolute of truth
  - lower bound must be > 0 and < 8 (Wilson CI never below 0 here)
  - upper bound must be > 15 and < 50 (asymmetric; Wald would give a
    much narrower band centred on the point)
  - upper - lower must be at least 15 pp (the Wald symmetric CI gives a
    smaller width, so this catches Wald)
"""
import json
import os

RESULT_FILE = "/output/result.json"
POINT_TRUTH = 8.10
POINT_ABS_TOL = 5.0
LOWER_RANGE = (0.0, 8.0)
UPPER_RANGE = (15.0, 50.0)
MIN_CI_WIDTH = 15.0


def _read():
    assert os.path.exists(RESULT_FILE), f"Missing {RESULT_FILE}"
    with open(RESULT_FILE) as f:
        return json.load(f)


def test_required_keys():
    d = _read()
    for k in ("prevalence", "ci_lower", "ci_upper"):
        assert k in d, f"Missing key {k!r}"


def test_point_value():
    v = float(_read()["prevalence"])
    assert abs(v - POINT_TRUTH) <= POINT_ABS_TOL, (
        f"prevalence={v}, expected {POINT_TRUTH} +/- {POINT_ABS_TOL}"
    )


def test_lower_bound_in_range():
    v = float(_read()["ci_lower"])
    assert LOWER_RANGE[0] <= v <= LOWER_RANGE[1], (
        f"ci_lower {v} not in {LOWER_RANGE}"
    )


def test_upper_bound_in_range():
    v = float(_read()["ci_upper"])
    assert UPPER_RANGE[0] <= v <= UPPER_RANGE[1], (
        f"ci_upper {v} not in {UPPER_RANGE}; for a Wilson CI on n_eff ~ 20 "
        "the upper bound should be much higher than for a symmetric Wald CI."
    )


def test_ci_brackets_point():
    d = _read()
    lo, p, hi = float(d["ci_lower"]), float(d["prevalence"]), float(d["ci_upper"])
    assert lo <= p <= hi, f"CI must bracket point ({lo} <= {p} <= {hi})"


def test_ci_width_sufficient():
    d = _read()
    width = float(d["ci_upper"]) - float(d["ci_lower"])
    assert width >= MIN_CI_WIDTH, (
        f"CI width {width:.2f} pp is suspiciously narrow for n_eff ~ 20. "
        "A naive Wald CI would be narrower; the Wilson-on-effective-n CI "
        "must be wider than {MIN_CI_WIDTH} pp here."
    )
