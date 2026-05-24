"""
Verifier for Task 4: Asian / White-non-Hispanic median household income ratio
(2023, CPS-ASEC).

Ground truth (Table A-1):
  Asian:                  $112,800
  White, not Hispanic:    $89,050
  Ratio = 112800 / 89050 = 126.67 %

Tolerance: +/- 1.5 percentage points absolute on the ratio. That covers
small rounding but rejects:
  - 133.33 % (using "White" row including Hispanic) -- diff 6.66 pp
  - 100.00 % (using Asian/Asian or White/White by mistake)
  -  63.43 % (Black / White-NH ratio swap)
"""
import os

RESULT_FILE = "/output/result.txt"
GROUND_TRUTH = 126.67
ABS_TOL = 1.5  # percentage points


def test_file_exists():
    assert os.path.exists(RESULT_FILE), f"Missing {RESULT_FILE}"


def test_parses_as_number():
    with open(RESULT_FILE) as f:
        raw = f.read().strip().replace(",", "").replace("%", "").replace("$", "")
    float(raw)


def test_value_within_tolerance():
    with open(RESULT_FILE) as f:
        raw = f.read().strip().replace(",", "").replace("%", "").replace("$", "")
    predicted = float(raw)
    lo, hi = GROUND_TRUTH - ABS_TOL, GROUND_TRUTH + ABS_TOL
    assert lo <= predicted <= hi, (
        f"Predicted {predicted}, expected {GROUND_TRUTH} +/- {ABS_TOL} "
        f"(range [{lo:.2f}, {hi:.2f}])"
    )


def test_not_using_white_overall_row():
    # 112800/84630 = 133.33% — the common error of using "White" (all,
    # including Hispanic) instead of "White, not Hispanic".
    with open(RESULT_FILE) as f:
        raw = f.read().strip().replace(",", "").replace("%", "").replace("$", "")
    predicted = float(raw)
    assert abs(predicted - 133.33) > 1.0, (
        f"Predicted {predicted}, which equals Asian / White (all races) "
        "ratio. The correct denominator is 'White, not Hispanic' (89,050), "
        "not 'White' (84,630)."
    )
