# Abundant Research take-home — Harbor DS Evals

A 10-task Harbor-format benchmark measuring where `gemini-3-flash-preview`
fails on documentation-grounded statistical analysis of U.S. federal survey
data (NHANES, NHIS, CPS-ASEC, NSF SDR, Census ASLGF).

The eval is a tightly scoped adaptation of the **LongDA** benchmark
(arXiv:2601.02598, Jan 2026) extended along two axes the authors named as
future work:

1. **Inferential statistics** — confidence intervals, hypothesis tests, and
   design-adjusted variance, not just point estimates.
2. **Multi-modal documentation hazards** — answers depend on information that
   only appears in charts or screenshots embedded in the federal publications.

## Repository layout

```
samples/                    10 Harbor-format tasks (escalating difficulty)
logs/                       Captured trial outputs from harbor runs (mirror of jobs/gemini)
report/                     Final write-up, figures, and per-task numbers
scripts/                    Helpers (data download, oracle/nop checks, trial runner)
_data_cache/                Raw federal data fetched once; copied into each task as needed
```

Per-task layout (canonical Harbor):

```
samples/task_NN_*/
├── instruction.md          Agent-facing problem statement
├── task.toml               Harbor task config (image, timeouts, metadata)
├── environment/
│   ├── Dockerfile          Sandbox base image (python:3.11-slim + deps)
│   └── data/               Survey data + codebook docs (PDF/HTML/PNG)
├── solution/solve.sh       Oracle solution; proves task is solvable
└── tests/
    ├── test.sh             Verifier entry point (pre-installed pytest)
    └── test_outputs.py     Per-task numerical/structural checks
```

## How the eval works

Every task asks the agent to compute a specific number (or a small structured
JSON) from a real public-use data file and write it to `/output/`. The data
file is paired with the official codebook/methodology documents the agency
ships alongside it. Verifiers compare against ground-truth values that are
published in the corresponding NCHS Data Brief, Census P60 report, NSF NCSES
table, or Census ASLGF brief. Tolerances follow the LongDA convention
(+/-5% relative for descriptive statistics; significance-category match for
p-values; wider tolerance for small-cell subgroup estimates).

## How to run

Prerequisites: Docker, Python 3.11+, Harbor 0.7+, and the federal data
files cached locally.

```bash
# 1) Fetch the data (one-time)
python scripts/download_federal_data.py

# 2) Copy data into each task's environment/data/
python scripts/scaffold_tasks.py

# 3) Generate the multi-modal PNGs used by tasks 7, 9, 10
python scripts/generate_multimodal_artifacts.py

# 4) Confirm Oracle=1.0 and Nop=0.0 on every task
bash scripts/run_oracle_nop_checks.sh

# 5) Run 3 attempts of Gemini Flash per task
GEMINI_API_KEY=<your-key> bash scripts/run_gemini_trials.sh

# 6) Compute pass@k and categorise failures
python scripts/compute_pass_at_k.py
python scripts/analyze_trajectories.py
```

## Known choices

- **Verifier strategy**: pytest plus `pytest-json-ctrf`, baked into each task
  image. Per-test assertions in `tests/test_outputs.py`; `tests/test.sh`
  writes a reward of `1` only if all tests pass.
- **Internet access in the agent environment**: enabled, because the Harbor
  gemini-cli adapter needs to apt-install curl and npm-install the gemini
  CLI. The gemini-cli tool does not have a web-search action by default, so
  the agent still has to do the actual computation from the local data.
- **NHANES variance estimation**: oracle solutions use Taylor-series
  linearization with `SDMVSTRA` / `SDMVPSU`. Verifiers accept any method
  that produces values inside the documented range (logit-CI, Wald-CI, and
  jackknife are all within tolerance).
- **NHIS variance estimation**: oracle uses `PSTRAT` / `PPSU` with Taylor
  linearization; same tolerance policy.

## Ground-truth sources

| Task | Source |
|------|--------|
| 1, 2, 3 | NCHS Data Brief No. 508, Table 1 |
| 4 | Census P60-282 Table A-1 |
| 5 | NHIS 2023 published chronic-pain estimate (24.3%) |
| 6 | NCHS Data Brief No. 508 (severe-obesity by sex panel) |
| 7 | NSF NCSES 25-321 Table 12-1 |
| 8 | Census 2021 ASLGF Table 1 (US state-and-local totals) |
| 9 | Computed from NHANES DR1TOT_L using WTDRD1 weights |
| 10 | NCHS Data Brief No. 508 (severe-obesity by sex and age panel) |
