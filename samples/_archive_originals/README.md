# Archived: Engineered Original Tasks

These three tasks were built from scratch using the same Adyen payments bundle
as the DABstep-wrapped tasks, with ground truth derived from
`scripts/dabstep_fee_engine.py`.

They were excluded from the active 25-task reproduction for the following reasons:

| Task | Reason |
|------|--------|
| `task_11_dabstep_orig_belles_total_2023` | Passed all 3 gemini-3-flash-preview trials — not useful as a difficulty signal |
| `task_12_dabstep_orig_belles_mcc_counterfactual` | Passed 2/3 trials — insufficient failure rate for failure-mode analysis |
| `task_14_dabstep_orig_crossfit_monthly_sd` | All 3 trials converged to a stable wrong answer; root cause is likely a coverage gap in the fee engine's monthly aggregation logic, not a model failure |

The fee engine (`scripts/dabstep_fee_engine.py`) is cross-validated against the
DABstep dev-split on 6 code paths. T14 appears to surface an uncovered edge case
(refused transactions in the monthly volume denominator). The task is archived
pending engine verification, not discarded.

The 5 DABstep-wrapped tasks in `_archive_dabstep_unselected/` were excluded for
a different reason: they passed during the original submission pilot and therefore
provide no failure signal.
