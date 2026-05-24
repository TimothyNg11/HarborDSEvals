"""
Verifier for Task 5: design-adjusted OR + Miettinen-Bruzzi PAF for
high-impact pain by age (65+ vs 18-44) among NHIS adults with chronic
pain.

Ground truth (NHIS 2023, messy data extract):
  OR = 1.70   PAF = 0.27 (proportion)

Tolerances:
  - odds_ratio within +/- 0.20 of 1.70 -> [1.50, 1.90]
  - PAF within +/- 0.06 of 0.27 -> [0.21, 0.33]
  - OR > 1 and PAF > 0 (older adults more likely to have high-impact pain)
"""
import json
import os

RESULT_FILE = "/output/result.json"
OR_TRUTH = 1.70
OR_TOL = 0.20
PAF_TRUTH = 0.27
PAF_TOL = 0.06


def _read():
    assert os.path.exists(RESULT_FILE), f"Missing {RESULT_FILE}"
    with open(RESULT_FILE) as f:
        return json.load(f)


def test_required_keys():
    d = _read()
    assert "odds_ratio" in d and "paf" in d


def test_odds_ratio_value():
    v = float(_read()["odds_ratio"])
    assert abs(v - OR_TRUTH) <= OR_TOL, (
        f"odds_ratio={v}, expected {OR_TRUTH} +/- {OR_TOL}"
    )


def test_or_greater_than_one():
    v = float(_read()["odds_ratio"])
    assert v > 1.0, f"odds_ratio={v}; expected > 1 (older adults more likely)"


def test_paf_value():
    v = float(_read()["paf"])
    assert abs(v - PAF_TRUTH) <= PAF_TOL, (
        f"paf={v}, expected {PAF_TRUTH} +/- {PAF_TOL}"
    )


def test_paf_positive():
    v = float(_read()["paf"])
    assert 0 < v < 1, f"paf={v} must be a positive proportion < 1"
