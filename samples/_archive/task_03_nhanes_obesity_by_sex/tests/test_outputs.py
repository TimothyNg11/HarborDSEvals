"""
Verifier for Task 3: age-standardized obesity rate ratio (NHB / NHW women).

Ground truth (computed from clean NHANES Aug 2021 - Aug 2023 women 20+
with Year-2000 standard population weights):
  nhb age-std obesity  = 55.03 %
  nhw age-std obesity  = 40.35 %
  rate ratio (NHB/NHW) =  1.3638

Tolerance:
  - Each std prevalence within +/- 3.0 pp.
  - Rate ratio within +/- 0.10 of truth.
  - Rate ratio must be > 1 (NHB > NHW; if reversed, races were swapped).
"""
import json
import os

RESULT_FILE = "/output/result.json"
TRUTH = {"nhb_std_prev": 55.03, "nhw_std_prev": 40.35, "rate_ratio": 1.3638}
ABS_TOL_PREV = 3.0
ABS_TOL_RATIO = 0.10


def _read():
    assert os.path.exists(RESULT_FILE), f"Missing {RESULT_FILE}"
    with open(RESULT_FILE) as f:
        return json.load(f)


def test_required_keys():
    d = _read()
    for k in TRUTH:
        assert k in d, f"Missing key {k!r}"


def test_nhb_std_prev():
    v = float(_read()["nhb_std_prev"])
    assert abs(v - TRUTH["nhb_std_prev"]) <= ABS_TOL_PREV, (
        f"nhb_std_prev={v}, expected {TRUTH['nhb_std_prev']} +/- {ABS_TOL_PREV}"
    )


def test_nhw_std_prev():
    v = float(_read()["nhw_std_prev"])
    assert abs(v - TRUTH["nhw_std_prev"]) <= ABS_TOL_PREV, (
        f"nhw_std_prev={v}, expected {TRUTH['nhw_std_prev']} +/- {ABS_TOL_PREV}"
    )


def test_rate_ratio():
    v = float(_read()["rate_ratio"])
    assert abs(v - TRUTH["rate_ratio"]) <= ABS_TOL_RATIO, (
        f"rate_ratio={v}, expected {TRUTH['rate_ratio']} +/- {ABS_TOL_RATIO}"
    )


def test_ratio_greater_than_one():
    v = float(_read()["rate_ratio"])
    assert v > 1.0, (
        f"rate_ratio={v}; NHB obesity prevalence is higher than NHW, so "
        "ratio must be > 1. A value < 1 indicates race codes were swapped."
    )
