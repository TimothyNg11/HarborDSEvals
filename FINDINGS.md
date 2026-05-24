# Findings: Where Flash-Class LLMs Fail on Documentation-Grounded Data Analysis

> **Status:** Sections 1–3 document the failure-mode analysis on the 10-task
> DABstep dev-split. Section 4 (intervention study) pre-registers a hypothesis
> here before the experiment is run — the result will be appended below the
> pre-registration. Section 5 (multi-model comparison: Gemini-3-Flash vs
> Claude-Haiku-4.5 on all 10 tasks) is filled in after Phase A2 completes.

---

## 1. Background

This document is the detailed companion to the top-level README. The paper
(`paper/main.pdf`) is the formal writeup; this document is the blog-post version
— more space for trajectory excerpts, edge-case reasoning, and honest accounting
of what went wrong.

**The short version of the story:**

I ran a federal-survey eval first — 10 tasks on NHANES/NHIS/CPS/NSF data,
weighted prevalences, design-adjusted confidence intervals, hypothesis tests,
the Erreygers concentration index. `gemini-3-flash-preview` passed every single
one, matching my oracle to ±0.0001 on the specialised stats. Bounded
single-statistic computation is no longer where flash-class models fail.

The literature is clear about where they do fail: multi-step planning over
heterogeneous data when the rules live in unstructured documentation and the
answer requires precise composition. DAB (Mar 2026): Gemini-3-Pro 38%,
Gemini-2.5-Flash 9%. DABstep (Jun 2025): best agent 16% overall, 14.55% on
hard split. GeneBench (Apr 2026): Gemini-3.1-Pro 11.2%. Same pattern across
three unrelated domains.

So I pivoted to DABstep's Adyen payments bundle. This document records what
I found.

---

## 2. The dominant failure mode — rule-precedence misread

Of the 5 original submission tasks that failed, 3 (T05, T06, T09) share a
single root cause. **Gemini reads the fee-rule manual and applies
"most-specific match wins" semantics when the manual specifies "every matching
rule applies."**

The specific sentence Gemini repeatedly fails to apply:

> *"If a field is set to null it means that it applies to all possible values
> of that field. E.g. null value in aci means that the rules applies for all
> possible values of aci."* — `manual.md` §5

The same applies to empty lists. This one sentence is the difference between
returning 6 fee IDs and 410 (T06), between a 19% overcount and the correct
average (T05), and between a -0.84 delta and -0.948 (T09).

### T06 — fee IDs for account_type=R, aci=B (pass@3 = 0 ✗)

This task is the cleanest demonstration of the failure. The correct answer is
410 fee IDs — every rule whose `account_type` and `aci` fields either contain
the target values or are null/empty. Gemini returned 6.

The correct interpretation: for a rule to apply to `account_type=R`, its
`account_type` field must be `["R"]`, `["R", "other"]`, `[]`, or `null`.
Gemini's interpretation: the `account_type` field must be literally `["R"]`.

The gap: 1.5% of the truth set. The miss is off by a factor of 68.

All three trials returned the same 6 IDs (`236, 368, 404, 539, 564, 757`) —
a stable, reproducible error, not noise.

### T05 — avg fee acc-H × MCC × GlobalCard, 10 EUR (pass@3 = 0 ✗)

**Correct:** `0.123217`
**Gemini said:** `0.167126`, `0.146937`, `0.147871`

All three trials sit 19–36% above truth. The trajectory shows Gemini
"matched 1,834 of 4,843 transactions to fee rules" — it was averaging over a
subset of transactions rather than averaging over rule rows. The same
null-means-any confusion is the underlying mechanism: the rule-matching was
too restrictive, so only a subset of applicable rules were found, and the
average over that subset skewed high.

### T09 — Belles delta if rule 384 rate=1 (pass@3 = 0 ✗)

**Correct:** `-0.94810300000017` (14 decimal places)
**Gemini said:** `-0.80054` (and similar values)

Gemini correctly identifies fee rule 384 but does not recompute the per-
transaction fee under the modified rule. The trajectory ends with a numeric
guess. The root cause is the same: the model doesn't know which transactions
rule 384 applies to (because null fields are misread), so it can't compute
the counterfactual total correctly.

---

## 3. The three smaller failure modes

### T03 — question-premise blindness (pass@3 = 0 ✗)

**Ask:** Is Martinis_Fine_Steakhouse in danger of a high-fraud-rate fine?
**Correct:** `Not Applicable`
**Gemini said:** `no`, `yes`, `no`

The `manual.md` discusses fraud levels affecting *fee brackets*, and §7.4
mentions PCI DSS *security compliance* penalties — but defines no "fine for
high fraud rate" mechanism. The correct answer is Not Applicable because the
question's premise does not exist in the rule system.

Gemini never validated the question's referent. It computed a fraud rate,
compared to a threshold it invented, and answered yes/no. This is a
semantic-miss failure: the model defaulted to the structure of the question
("is X in danger of Y?") without checking whether Y exists.

### T10 — combinatorial-planning failure (pass@3 = 0 ✗)

**Ask:** Which ACI should we incentivize Belles's fraudulent transactions
toward to minimise total fees? Format `{ACI}:{fee_to_2dp}`.
**Correct:** `E:13.57`
**Gemini said:** `B:71.58` (and similar wrong-ACI answers)

The task requires evaluating 7 ACIs (A–G), computing total fees under each
substitution, and picking the minimum. Gemini evaluated only 3 ACIs (A, B, C)
— the ones listed first in the manual or in the data. It never reached E.

The model collapsed a 7-branch combinatorial search into a 3-branch one by
pruning the search space based on a heuristic (likely: "POS transactions only"
or "first N encountered"). This is a planning failure: correct algorithm,
insufficient search depth.

---

## 4. Intervention study

### 4.1 Pre-registration

**This subsection is committed to the repository BEFORE the intervention
runs. The git history is the provenance — `git log FINDINGS.md` should show
this commit landed before the `feat: rule-precedence prompt intervention`
commits below it.**

**Hypothesis (pre-registered):** Adding a single rule-semantics block to the
top of each task's `instruction.md` closes **≥ 25 percentage points on
aggregate pass@3** across the 5 rule-precedence tasks (T05, T06, T07, T08,
T09), for **both** `gemini-3-flash-preview` and `claude-haiku-4-5-20251001`.

**Tasks selected for the intervention arm:** The 5 fee-rule / fee-ID
intersection tasks in the 10-task set — T05, T06, T07, T08, T09 — chosen
because they are the cleanest test of the rule-precedence-misread mechanism
described in §2. T03 (semantic) and T10 (combinatorial) are deliberately
excluded: their failure mechanisms (§3) are different and the intervention
should not affect them.

**Intervention:** Prepend this verbatim block to `instruction.md` for each of
the 5 tasks. No other file (verifier, `task.toml`, solution, environment)
changes, so any pass@3 delta attributes cleanly to the prompt:

> **Important rule-matching semantics for fee rules in `/data/fees.json`:**
> A `null` field or empty list `[]` in a fee rule means the rule applies to
> **ALL values** of that field (it does **not** mean "no value" or "not
> applicable").
> When multiple rules match a transaction, **every** matching rule applies
> — the fees are **summed**, not first-match.

The verbatim block is also committed at
[`results/intervention_prompt.diff`](results/intervention_prompt.diff).

**Falsifiable predictions:**

- **If the failure is a knowledge gap** (the model never had the rule semantics
  internalised in the first place): intervention closes ≥ 25 pp on aggregate
  pass@3 across the 5 tasks for both models. Knowledge-gap framing wins.
- **If the failure is a capability gap** (the model can read the sentence but
  can't reliably apply it at this compositional depth): intervention closes
  < 10 pp, or shows only one model improving. Capability-gap framing wins.
- **Mixed outcome** (intervention helps Haiku more than Gemini, or vice versa,
  or some tasks but not others): documented as such — the binary framing
  doesn't apply uniformly.

Outcome direction is reported **honestly regardless of sign**. A null or
negative result is also a finding.

### 4.2 Results

> *[To be filled after `scripts/run_intervention.sh` completes. See
> `results/intervention.csv` and `report/figures/intervention_delta.png`.]*

---

## 5. Multi-model comparison

**Models:** `gemini-3-flash-preview`, `claude-haiku-4-5-20251001` (via Harbor's
built-in `claude-code` agent).

**Tasks:** 10 DABstep dev-split tasks (the existing wrapped set in `samples/`).

**Key questions:**
- Does Haiku exhibit the same rule-precedence misread as Gemini?
- Is the failure mode model-family-specific, or universal across flash-class
  models?
- Do the two models share the same failure distribution, or does each have a
  distinct profile?

**Results:** *[To be filled after Haiku baseline completes. See
[`results/multimodel_baseline.csv`](results/multimodel_baseline.csv) and
[`report/figures/multimodel_heatmap.png`](report/figures/multimodel_heatmap.png).]*

---

## 6. Summary and implications

> **[Filled in after Phases A2 (Haiku baseline) and B3 (intervention) complete.]**

Depending on the intervention result:

**If intervention works:** The dominant failure mode is a knowledge gap about
one convention in one rule system. This implies:
- Flash-class models can handle the *computation* required for multi-step fee
  aggregation if they apply the right rules.
- The failure in these benchmarks (DABstep, DAB) is not a capability ceiling;
  it's a documentation-grounding failure.
- Better prompting or RAG over the rule manual may be sufficient for production
  deployments.

**If intervention does not work:** The dominant failure mode is a capability
gap. The model cannot reliably apply a rule it was just told, at this level of
compositional complexity. This implies:
- Prompt engineering is insufficient.
- The correct fix is scaffolding (e.g., structured rule-extraction step before
  computation), tool use, or a stronger model.

---

## Appendix: Cross-validation and engine trust

See [ENGINE.md](ENGINE.md) for the full cross-validation methodology. In short:
the engine matches 6/6 DABstep dev-split questions on the code paths that matter
for the active tasks. Two bugs were found and fixed during development. The
archived T14 task surfaced a potential gap in monthly aggregation logic; that
task is excluded from the active set pending investigation.

The intervention study uses the DABstep paper's published answers as ground
truth — not the engine. Engine cross-validation is relevant only for
establishing that the failure modes identified in the original 8-task submission
are real: they survive the cross-validation check.
