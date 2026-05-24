# Scripts

All automation lives here. Grouped by purpose.

---

## Core engine

| Script | What it does |
|--------|-------------|
| `dabstep_fee_engine.py` | Deterministic implementation of DABstep manual's rule-matching semantics. See [ENGINE.md](../ENGINE.md) for documentation. |
| `cross_validate_engine.py` | Validates the engine against 6 DABstep dev-split questions with published answers. Run to verify correctness after any engine change. |

---

## Task construction

| Script | What it does |
|--------|-------------|
| `build_dabstep_tasks.py` | Wraps DABstep dev-split questions into Harbor format (Dockerfile, task.toml, instruction.md, solution/solve.sh, tests/test_outputs.py). Phase 2 extends this to 25 tasks. |
| `build_original_hard_tasks.py` | Built the 3 engineered original tasks (now archived). Kept as reference for the task-construction pattern. |
| `scaffold_tasks.py` | Copies data files from `_data_cache/` into each task's `environment/data/`. Run after `build_dabstep_tasks.py`. |
| `download_federal_data.py` | Downloads NHANES/NHIS/CPS federal survey data for the original pilot (no longer needed for the active DABstep eval). |
| `generate_multimodal_artifacts.py` | Generates PNG screenshots for the federal-survey pilot tasks (no longer active). |
| `make_messy_data.py` | Introduces realistic data-quality issues into the Adyen CSV bundle for hardened task variants. |
| `swap_in_messy_data.py` | Substitutes the messy bundle into task `environment/data/`. Companion to `make_messy_data.py`. |
| `compute_hard_ground_truths.py` | Computes ground-truth answers for tasks requiring multi-step fee aggregation. |
| `compute_hard_stat_ground_truths.py` | Computes ground-truth answers for tasks requiring statistical computation over fees (SD, percentiles). |
| `verify_ground_truth.py` | Spot-checks computed ground truths against manual calculations. |
| `verify_messy_ground_truth.py` | Same check applied to the messy-data task variants. |

---

## Running trials

| Script | What it does |
|--------|-------------|
| `run_oracle_nop_checks.sh` | Runs each task's oracle solution (expect reward 1.0) and the no-op agent (expect reward 0.0) via Harbor. Must pass before any model trial. |
| `run_gemini_trials.sh` | Runs gemini-3-flash-preview on every task, 3 trials each. Requires `GEMINI_API_KEY`. Logs raw Harbor output to `jobs/gemini/`. |
| `mirror_trials_to_logs.py` | Copies cleaned trial outputs from `jobs/gemini/` to `logs/` in the format the submission brief requires. |

---

## Analysis

| Script | What it does |
|--------|-------------|
| `compute_pass_at_k.py` | Reads verifier rewards from `jobs/` and computes pass@1, pass@3 per task and in aggregate. Writes a summary table. |
| `reevaluate_trials.py` | Re-runs pytest verifiers on existing agent outputs without re-running the agent. Useful after a verifier fix. |
| `analyze_trajectories.py` | Reads ATIF-format agent trajectories from `jobs/*/agent/`, classifies each failure by mode (semantic miss, implicit rule, etc.), writes `report/data/failure_categorization.csv`. |
| `categorize_failures_manual.py` | Interactive helper for manually labelling failure modes when trajectory parsing is ambiguous. |
| `inspect_trial_outputs.py` | Prints the agent's final answer and verifier reward for a given task+trial. Quick inspection without reading raw JSON. |

---

## Report generation

| Script | What it does |
|--------|-------------|
| `generate_report_figures.py` | Generates `difficulty_curve.png` and the original `failure_taxonomy.png` from `report/data/`. |
| `generate_corrected_failure_pie.py` | Generates `failure_taxonomy_v2.png` — the root-cause 4-slice view with rule-precedence as the dominant mode (~47%). |

---

## Packaging

| Script | What it does |
|--------|-------------|
| `build_submission_zip.py` | Packages `samples/`, `logs/`, and `report/` into `submission.zip` in the format the submission brief specifies. |
| `finalize_deliverable.py` | Last-mile checks before submission: verifies oracle/nop pass, checks report completeness, confirms zip is valid. |
