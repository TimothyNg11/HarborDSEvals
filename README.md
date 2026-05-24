# DABstep Reproduction — Where Flash-Class LLMs Fail on Documentation-Grounded Data Analysis

A Harbor-format reproduction of the DABstep dev split (arXiv:2506.23719) on
two flash-class LLMs — `gemini-3-flash-preview` and `claude-haiku-4-5` —
plus a pre-registered intervention study targeting the dominant failure mode.

> **TL;DR:** Both flash-class models score the same on the 10-task DABstep
> dev split (50 % pass@3, identical aggregate). The pre-registered
> single-sentence prompt intervention does **not** clear the predicted
> 25 pp bar on pass@3, but it sharply improves *consistency*: Gemini's
> pass@1 jumps 0 % → 100 % on T07–T08, Haiku's pass@1 on T06 goes 33 % →
> 100 %. The full read: rule-precedence misread is a knowledge gap on
> pure rule-intersection tasks (T06–T08) and a residual capability gap on
> compound tasks that layer additional computation on top (T05, T09).

---

## Results

### Multi-model baseline — 10 dev-split tasks

| Model | Aggregate pass@3 | Aggregate pass@1 |
|-------|:----------------:|:----------------:|
| `gemini-3-flash-preview`    | **50 %** (5/10) | 20 % (2/10) |
| `claude-haiku-4-5-20251001` | **50 %** (5/10) | 20 % (2/10) |

Per-task matrix in [`results/multimodel_baseline.csv`](results/multimodel_baseline.csv).
Both models fail on the same five tasks (T03, T05, T09, T10, plus T02 for
Haiku / T06 for Gemini). Bottleneck is the documentation-grounding pattern,
not the model.

![Multi-model heatmap](report/figures/multimodel_heatmap.png)

### Intervention study — 5 rule-precedence tasks (T05–T09)

**Pre-registered hypothesis** (committed to [FINDINGS.md §4.1](FINDINGS.md#4-intervention-study)
before runs landed): a 6-line rule-semantics prompt closes ≥ 25 pp on
aggregate pass@3 across T05–T09 for both models.

**Result: hypothesis failed at pass@3 — but per-trial deltas are large.**

| Model | Baseline pass@3 | Intervention pass@3 | Δ |
|-------|:---------------:|:-------------------:|:--:|
| `gemini-3-flash-preview` | 40 % (2/5) | 40 % (2/5) | **+0 pp** |
| `claude-haiku-4-5`       | 60 % (3/5) | 40 % (2/5) | **−20 pp** |

**Per-trial pass counts (n = 3) on the 5 intervention tasks:**

| Task | Gemini base | Gemini intv | Haiku base | Haiku intv |
|------|:-----------:|:-----------:|:----------:|:----------:|
| T05  | 0/3 | 0/3 | 0/3 | 0/3 |
| T06  | 0/3 | 0/3 | 1/3 | **3/3** ✅ |
| T07  | 1/3 | **3/3** ✅ | 1/3 | 0/3 |
| T08  | 1/3 | **3/3** ✅ | 1/3 | 1/3 |
| T09  | 0/3 | 0/3 | 0/3 | 0/3 |

Three cells go from "lucky pass" to "deterministic pass" (Gemini T07/T08,
Haiku T06). Two cells (T05, T09) remain stuck — these layer additional
computation on top of rule matching, where the prompt clarification is
necessary but not sufficient. Full discussion in
[FINDINGS.md §4.2–4.3](FINDINGS.md#42-results).

![Intervention delta](report/figures/intervention_delta.png)

Verbatim intervention prompt: [`results/intervention_prompt.diff`](results/intervention_prompt.diff).

---

## Figures

![Difficulty curve](report/figures/difficulty_curve.png)

*Pass@3 per task, original 5-task set. Six of eight original tasks score 0.*

![Failure taxonomy](report/figures/failure_taxonomy_v2.png)

*Root-cause taxonomy. Rule-precedence misread (T05, T06, T09) accounts for ~47%
of failures on the original set — more with the expanded 25-task corpus.*

---

## What this is

**Framework:** [Harbor](https://github.com/av/harbor) — an eval orchestrator
for data-science agents. Each task is a directory containing a Dockerfile,
a `task.toml` config, an `instruction.md` for the agent, a `solution/solve.sh`
oracle, and a `tests/test_outputs.py` pytest verifier. Harbor runs the agent in
a sandboxed Docker container; the verifier reads `/output/answer.txt` and emits
a binary reward.

**Dataset:** Adyen payments scenario from DABstep (CC-BY-4.0). 138K synthetic
payment transactions, 1000 fee rules, 30 merchants, and a 5-page markdown
rule manual with implicit semantics. Same bundle across all 10 tasks.

**Agents under test:**
- `gemini-3-flash-preview` via Harbor's `gemini-cli` agent.
- `claude-haiku-4-5-20251001` via Harbor's built-in `claude-code` agent
  (no custom adapter needed — Harbor ships with first-class Claude Code
  support).

**Ground truth:** DABstep's published answers for all 10 dev-split tasks.
The fee engine ([ENGINE.md](ENGINE.md)) is a separate engineering artifact
used to validate the rule-matching interpretation independently.

**Verifier:** Deterministic pytest. Numeric answers are compared to tolerance
(4–14 decimal places, following DABstep's answer-format spec). Set answers
require exact membership equality. No LLM-as-judge — reward signal must be
clean for downstream RL use.

---

## Why it's interesting

Most benchmarks treat failures as opaque pass/fail numbers. This repo treats
failures as *diagnostic signals*.

**The pivot story.** The original pilot eval — 10 tasks on federal survey data
(NHANES, NHIS, CPS-ASEC, NSF SDR) — was passed entirely by
`gemini-3-flash-preview`. Weighted prevalences, design-adjusted CIs, hypothesis
tests, the Erreygers concentration index. Bounded single-statistic computation
is no longer a flash-class failure mode. The literature (DAB, DABstep,
GeneBench, scBench) converges on a different failure shape: multi-step planning
over heterogeneous data when rules live in unstructured documentation.

**The dominant failure mode.** On the original 5 failing tasks, ~47% of
failures trace to one misread sentence in the manual:

> *"If a field is set to null it means that it applies to all possible values
> of that field."* — `manual.md` §5

Gemini reads this as "most-specific match wins." The manual means "every
matching rule applies, and empty/null fields match everything." T06 surfaces
this most cleanly: 6 fee IDs returned vs. 410 correct — a 68× undershoot.

**The intervention study.** We test whether adding a one-sentence clarification
to the system prompt closes the gap. If yes: the failure is a knowledge gap
(cheap to fix). If no: the failure is a capability gap (requires more than
prompt engineering). Either result is a concrete finding. See [FINDINGS.md](FINDINGS.md).

---

## Methodology

### Task construction

Tasks are Harbor-wrapped DABstep hard-split questions. Each task:
- Uses the same Adyen data bundle (no per-task data download)
- Has an oracle solution (`solution/solve.sh`) that produces the exact correct
  answer — verified at reward 1.0 before any model trial
- Has a nop agent that writes nothing — verified at reward 0.0
- Has a deterministic pytest verifier that checks the agent's answer

```
samples/task_NN_dabstep_*/
├── instruction.md          agent-facing problem statement
├── task.toml               Harbor config (image, timeouts, metadata)
├── environment/
│   ├── Dockerfile          python:3.11-slim + pandas + numpy + misc
│   └── data/               payments.csv, fees.json, merchant_data.json, manual.md
├── solution/solve.sh       oracle (writes the correct answer)
└── tests/
    ├── test.sh             verifier entry point
    └── test_outputs.py     pytest assertions (exact match or ±tolerance)
```

### Ground-truth engine

`scripts/dabstep_fee_engine.py` is a deterministic Python implementation of the
manual's semantics. It was used for the archived engineered originals (T11,
T12, T14) and is cross-validated 6/6 against DABstep dev-split published
answers. See [ENGINE.md](ENGINE.md).

### Intervention

The intervention prepends a 6-line rule-semantics block to `instruction.md`
for the 5 selected rule-precedence tasks (T05–T09). Every other file in the
task directory (verifier, `task.toml`, solution, environment) is
byte-identical to the baseline, so any pass@3 delta attributes cleanly to
the prompt change. The verbatim block is committed at
[`results/intervention_prompt.diff`](results/intervention_prompt.diff). See
[FINDINGS.md §4](FINDINGS.md#4-intervention-study) for pre-registration and
the result.

---

## Repository layout

```
samples/                              10 active DABstep dev-split tasks
  _archive_originals/                 3 archived engineered originals
  _archive_dabstep_unselected/        Earlier-trial passing tasks
  _archive_hardsplit_unfinished/      15 hard-split tasks scaffolded but
                                      never finished (no public ground truth)
samples_intervention/                 5 tasks (T05-T09) with rule-semantics
                                      block prepended to instruction.md
scripts/                              Automation (see scripts/README.md)
  load_env.sh                         Source-able .env loader
  run_gemini_trials.sh                Gemini baseline runner
  run_haiku_baseline.sh               Haiku baseline runner
  run_intervention.sh                 Intervention runner (both models)
  build_intervention_set.py           Builds samples_intervention/
  compute_results.py                  CSVs from job dirs
  make_result_figures.py              Heatmap + intervention bar chart
results/                              CSVs + prompt diff
  multimodel_baseline.csv             10-task × 2-model pass@1/pass@3
  intervention.csv                    5-task × 2-model baseline vs intervention
  intervention_prompt.diff            verbatim 6-line block
  per_task_rewards.json               raw rewards array per cell
report/
  report.md                           Original 8-task submission report
  figures/                            PNG figures
paper/                                LaTeX paper source + Makefile
jobs/                                 Raw Harbor outputs
  gemini/                             Gemini baseline trials
  haiku/                              Haiku baseline trials
  intervention_gemini/                Gemini intervention trials
  intervention_haiku/                 Haiku intervention trials
submission/                           Frozen original 8-task submission
_data_cache/                          Raw DABstep dataset (gitignored)
```

---

## Reproducibility

```bash
# 1. Install dependencies (requires Python 3.11+, Docker, Harbor)
pip install -r requirements.txt

# 2. Set API keys in a .env file (gitignored). Format: KEY = value
echo 'GEMINI_API_KEY = ...' > .env
echo 'ANTHROPIC_API_KEY = ...' >> .env

# 3. Cross-validate the fee engine (6/6 against DABstep dev-split)
python scripts/cross_validate_engine.py

# 4. Run gemini-3-flash-preview baseline (3 trials × 10 tasks)
bash scripts/run_gemini_trials.sh

# 5. Run claude-haiku-4-5 baseline (3 trials × 10 tasks)
bash scripts/run_haiku_baseline.sh

# 6. Build intervention task variants (samples_intervention/)
python scripts/build_intervention_set.py

# 7. Run intervention on both models (3 trials × 5 tasks × 2 models)
bash scripts/run_intervention.sh   # or: scripts/run_intervention.sh gemini

# 8. Aggregate CSVs + figures
python scripts/compute_results.py
python scripts/make_result_figures.py

# 9. Build the paper PDF (requires TeXLive / MiKTeX)
cd paper && make pdf
```

Total run-time: ~2-4 hours wall-clock at 2 concurrent trials.
Total cost: ~$20 across both APIs (Gemini + Anthropic).

---

## References

| Paper | Venue | Headline |
|-------|-------|---------|
| [DABstep](https://arxiv.org/abs/2506.23719) | Jun 2025 | Best agent 16% overall, 14.55% hard split. Source of the 25 tasks and data bundle. |
| [DAB](https://arxiv.org/abs/2603.20576) | Mar 2026 | Gemini-3-Pro 38%, Gemini-2.5-Flash 9%. Establishes flash-class failure on this task shape. |
| [GeneBench](https://www.biorxiv.org/content/10.1101/2026.04.22.720113) | Apr 2026 | Gemini-3.1-Pro 11.2%. Confirms failure generalises to genomics domain. |
| [scBench](https://arxiv.org/abs/2602.09063) | Feb 2026 | Top model 52.8%. Heterogeneous data + implicit rules shape in single-cell biology. |
| [LongDA](https://arxiv.org/abs/2601.02598) | Jan 2026 | Long-context data analysis failure modes. Informed task-shape selection. |
| DSAEval | Jan 2026 | Data science agent evaluation taxonomy. Failure-mode vocabulary. |
| DSGym | Jan 2026 | Multi-task DS evaluation framework. Taxonomy structure. |

---

## License

Code: MIT. See [LICENSE](LICENSE).

Dataset: The Adyen payments bundle (`payments.csv`, `fees.json`,
`merchant_data.json`, `manual.md`) is from the DABstep benchmark and licensed
under CC-BY-4.0. The MIT license for this repository applies to the code only,
not the dataset.
