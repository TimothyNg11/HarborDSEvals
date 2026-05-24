"""
Verifier for Task 7: CS share of industry-employed doctorates (NSF SDR 2023).

Ground truth (Table 12-1, "All fields" + "Computer and information sciences"
rows, with industry defined by the bundled figure as Private-for-profit +
Self-employed):

  industry total       = 396,450
  CS in industry       = 21,550        ( = 20,800 + 750 )
  share                = 21,550 / 396,450 = 5.44 %

Tolerance: +/- 0.7 pp absolute. This excludes likely wrong answers:
  - 5.24 %  ( CS-in-for-profit / for-profit-all-fields = 20800/354100 )
  - 4.00 %  ( CS-all-sectors / all-doctorates = 36350/908700 )
  - 6.34 %  ( CS-in-for-profit / industry = 20800/396450, using all CS but
              only for-profit denominator -- inconsistent )
"""
import os

RESULT_FILE = "/output/result.txt"
GROUND_TRUTH = 5.44
ABS_TOL = 0.7


def test_file_exists():
    assert os.path.exists(RESULT_FILE), f"Missing {RESULT_FILE}"


def test_parses_as_number():
    with open(RESULT_FILE) as f:
        raw = f.read().strip().replace(",", "").replace("%", "")
    float(raw)


def test_value_within_tolerance():
    with open(RESULT_FILE) as f:
        predicted = float(f.read().strip().replace(",", "").replace("%", ""))
    lo, hi = GROUND_TRUTH - ABS_TOL, GROUND_TRUTH + ABS_TOL
    assert lo <= predicted <= hi, (
        f"Predicted {predicted}, expected {GROUND_TRUTH} +/- {ABS_TOL} "
        f"(range [{lo:.2f}, {hi:.2f}])"
    )


def test_not_cs_over_all_doctorates():
    # 36350/908700 = 4.00% -- agent used "All fields" denominator,
    # ignoring the industry restriction.
    with open(RESULT_FILE) as f:
        predicted = float(f.read().strip().replace(",", "").replace("%", ""))
    assert abs(predicted - 4.00) > 0.2, (
        f"Predicted {predicted}, which equals CS-over-all-doctorates. "
        "The denominator must be industry-employed doctorates only."
    )
