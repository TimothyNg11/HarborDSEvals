"""
Verifier for Task 2: age-standardized obesity prevalence by education
(Year-2000 standard population, age bands 20-39, 40-59, 60+).

Ground truth (computed from clean NHANES Aug 2021 - Aug 2023, age 25+,
DMDEDUC2 1-5):
  low_ed (HS or less) age-std obesity  = 47.01 %
  high_ed (>= some college)            = 39.22 %
  rate difference                       =  7.78 pp

Tolerance:
  - Each std prevalence within +/- 2.0 pp.
  - Rate difference within +/- 2.5 pp.
  - Difference must be POSITIVE (low > high). If agent reported crude
    rates instead, the rate difference is typically 5.5-6.5 pp -- still
    likely to pass, but the std-prev tests will fail because crude
    values differ from std values by more than 2.0 pp in at least one
    band.
"""
import json
import os

RESULT_FILE = "/output/result.json"
TRUTH = {"low_ed_std_prev": 47.01, "high_ed_std_prev": 39.22, "rate_difference": 7.78}
ABS_TOL_PREV = 2.0
ABS_TOL_DIFF = 2.5


def _read():
    assert os.path.exists(RESULT_FILE), f"Missing {RESULT_FILE}"
    with open(RESULT_FILE) as f:
        return json.load(f)


def test_required_keys():
    d = _read()
    for k in TRUTH:
        assert k in d, f"Missing key {k!r}"


def test_low_ed_std_prev():
    v = float(_read()["low_ed_std_prev"])
    assert abs(v - TRUTH["low_ed_std_prev"]) <= ABS_TOL_PREV, (
        f"low_ed_std_prev={v}, expected {TRUTH['low_ed_std_prev']} +/- {ABS_TOL_PREV}"
    )


def test_high_ed_std_prev():
    v = float(_read()["high_ed_std_prev"])
    assert abs(v - TRUTH["high_ed_std_prev"]) <= ABS_TOL_PREV, (
        f"high_ed_std_prev={v}, expected {TRUTH['high_ed_std_prev']} +/- {ABS_TOL_PREV}"
    )


def test_rate_difference():
    v = float(_read()["rate_difference"])
    assert abs(v - TRUTH["rate_difference"]) <= ABS_TOL_DIFF, (
        f"rate_difference={v}, expected {TRUTH['rate_difference']} +/- {ABS_TOL_DIFF}"
    )


def test_difference_sign():
    v = float(_read()["rate_difference"])
    assert v > 0, (
        "Rate difference (low minus high education) must be positive; "
        "if reversed, education levels were swapped."
    )
