"""
Verifier for Task 8: state vs local share of US-total tax revenue (2021).

Ground truth (Census ASLGF Table 1, "Taxes" row, US columns):
  total state+local taxes:   $2,103,195,606 thousand
  state taxes:               $1,262,528,447 thousand   =>  60.03 %
  local taxes:               $  840,667,159 thousand   =>  39.97 %

Tolerance: +/- 1.5 pp absolute per share. Sum within 0.2 pp of 100.

Likely wrong answers caught:
  - 50/50 (agent split arbitrarily without reading the column structure)
  - 27.6 % / 72.4 % (intergovernmental share / not-intergovt mistakenly)
  - 100/0 or 0/100 (agent used the state-only or local-only column only)
"""
import json
import os

RESULT_FILE = "/output/result.json"
TRUTH = {"state_share": 60.03, "local_share": 39.97}
ABS_TOL = 1.5


def _read():
    assert os.path.exists(RESULT_FILE), f"Missing {RESULT_FILE}"
    with open(RESULT_FILE) as f:
        return json.load(f)


def test_required_keys():
    d = _read()
    for k in TRUTH:
        assert k in d, f"Missing key {k!r}"


def test_state_share():
    v = float(_read()["state_share"])
    assert abs(v - TRUTH["state_share"]) <= ABS_TOL, (
        f"state_share={v}, expected {TRUTH['state_share']} +/- {ABS_TOL}"
    )


def test_local_share():
    v = float(_read()["local_share"])
    assert abs(v - TRUTH["local_share"]) <= ABS_TOL, (
        f"local_share={v}, expected {TRUTH['local_share']} +/- {ABS_TOL}"
    )


def test_sum_close_to_100():
    d = _read()
    s = float(d["state_share"]) + float(d["local_share"])
    assert 99.8 <= s <= 100.2, (
        f"state_share + local_share = {s:.2f}; must equal 100% (state+local "
        "must be exhaustive)."
    )
