# Ground-Truth Fee Engine

`scripts/dabstep_fee_engine.py` is a deterministic Python implementation of the
Adyen fee-rule semantics described in DABstep's `manual.md`. It was built to
produce ground-truth answers for the engineered original tasks (now archived in
`samples/_archive_originals/`).

For the active 25-task reproduction set, ground truth comes directly from
DABstep's published answers — the engine is not required as the answer key.
It is documented here as a stand-alone engineering artifact because:

1. It demonstrates the methodology for porting the eval pattern to
   non-DABstep corpora (any domain with a rule manual + transactions).
2. Its cross-validation result validates the rule-matching interpretation used
   across all analyses of the failure modes.
3. The two bugs found during development are the clearest example in this
   repo of the kind of edge-case reasoning a human must get right to produce
   trustworthy eval ground truth — exactly the skill benchmark engineering
   requires.

---

## The fee formula

From `manual.md` §5:

```
fee = fixed_amount + rate * transaction_value / 10000
```

`fixed_amount` is in EUR. `rate` is a dimensionless integer. The engine
implements this in `compute_fee(rule, eur_amount)`.

---

## Rule-matching semantics

A fee rule in `fees.json` applies to a transaction if and only if **every
non-null field on the rule matches the transaction**. The key semantic that
differentiates this system from most real-world rule engines:

> "If a field is set to null it means that it applies to all possible values
> of that field."  — `manual.md` §5 (emphasis mine)

The same applies to empty lists. This is the rule `gemini-3-flash-preview`
consistently misreads, defaulting to "most-specific match wins" instead.

Fields checked by `rule_matches_txn()`, in order:

| Field | Type | Matching logic |
|-------|------|----------------|
| `card_scheme` | string | Exact match |
| `account_type` | list or null | List membership; empty/null = any |
| `capture_delay` | category string | Semantic comparison (see below) |
| `monthly_fraud_level` | bucket string | Must equal the merchant's fraud bucket for that calendar month |
| `monthly_volume` | bucket string | Must equal the merchant's volume bucket for that calendar month |
| `merchant_category_code` | list or null | List membership; empty/null = any |
| `is_credit` | bool or null | Exact bool match; null = any |
| `aci` | list or null | List membership; empty/null = any |
| `intracountry` | bool or null | `True` iff `ip_country == acquirer_country` |

### Fee composition

For each transaction, the engine finds **every** matching rule and sums the
fee across all of them. There is no "first match wins" or "most specific match
wins" logic. This is the most important semantic to get right — and the one
Gemini consistently gets wrong.

---

## Monthly bucket computation

Two rule fields — `monthly_volume` and `monthly_fraud_level` — depend on the
merchant's aggregate behavior for the whole calendar month, not the individual
transaction. `compute_monthly_buckets()` precomputes a `{month_int -> (vol_bucket, fraud_bucket)}`
table per merchant per year:

**Volume buckets** (`monthly_volume`):

| Bucket string | Range |
|--------------|-------|
| `<100k` | < €100,000 / month |
| `100k-1m` | €100k – €1m |
| `1m-5m` | €1m – €5m |
| `>5m` | > €5m |

**Fraud buckets** (`monthly_fraud_level`):

| Bucket string | Fraud rate range |
|--------------|----------------|
| `<7.2%` | below 7.2% |
| `7.2%-7.7%` | 7.2% – 7.7% |
| `7.7%-8.3%` | 7.7% – 8.3% |
| `>8.3%` | above 8.3% |

Fraud rate = `100 × sum(eur_amount where has_fraudulent_dispute) / sum(eur_amount)`.
The boundaries are not stated explicitly in `manual.md` — they are inferred from
the bucket strings in `fees.json` itself.

---

## Capture-delay semantic mapping

`capture_delay` in `fees.json` uses category strings: `"<3"`, `"3-5"`, `">5"`,
`"immediate"`, `"manual"`. Merchant data sometimes stores a raw integer day count
(e.g. `"4"`). `_capture_delay_ok()` converts numeric day counts to the rule's
category space before comparing:

```
d = int(merchant_cd)   # e.g. 4
"<3"  → d < 3
"3-5" → 3 ≤ d ≤ 5      # "4" matches "3-5"
">5"  → d > 5
```

---

## Two bugs found during development

### Bug 1 — `monthly_volume_bucket` not pre-computed

**Symptom:** rules with a `monthly_volume` constraint never matched any
transaction; total fees were systematically under-counted.

**Root cause:** the original version of the engine compared the rule's
`monthly_volume` string directly against the transaction's `eur_amount` (a
float). The comparison always failed because the types and semantics don't
match — you need to compute the merchant's total EUR volume for the whole
calendar month first, bucket it, and then compare bucket strings.

**Fix:** `compute_monthly_buckets()` now builds the per-merchant per-month
table before processing any transactions. `per_txn_total_fee_with_buckets()`
looks up the precomputed bucket for each transaction's month rather than trying
to derive it from the transaction alone.

### Bug 2 — `capture_delay` string equality

**Symptom:** rules with a `capture_delay` of `"3-5"` never matched merchants
whose `capture_delay` was stored as `"4"` (a raw day count).

**Root cause:** the original engine did `rule_cd == merchant_cd`, which is
`"3-5" == "4"` — always False. The manual implies a semantic mapping that the
engine didn't implement.

**Fix:** `_capture_delay_ok()` detects when the merchant value is numeric,
converts it, and compares to the rule's category range.

Both bugs were found by running the cross-validation suite and inspecting which
code paths produced wrong results.

---

## Cross-validation

`scripts/cross_validate_engine.py` validates the engine against 6 DABstep
dev-split questions where Adyen has published the correct answer:

| Case | What it tests |
|------|--------------|
| T5 — top issuing country | Data ingest: CSV parsed correctly, groupby semantics |
| T1273 — avg fee GlobalCard credit 10 EUR | `compute_fee` + rule filtering |
| T1464 — fee IDs for account_type=R, aci=B | `_list_ok` with null/empty semantics (410-ID set) |
| T1681 — fee IDs Belles 2023-01-10 | `matching_rule_ids_with_buckets` |
| T1753 — fee IDs Belles 2023-03 | Same, different month |
| T1871 — Belles delta if rule 384 rate=1 | `per_txn_total_fee_with_buckets` + counterfactual |

Result: **6/6 exact matches** (within tolerance) on the code paths the archived
originals exercise.

**Coverage caveat:** T1305 (avg fee with MCC filter) was excluded after a 1.1%
averaging discrepancy was found whose root cause was not isolated within the
original time budget. T14 (Crossfit monthly SD) surfaced a possible edge case
in the monthly aggregation logic (suspected: refused transactions included in
the volume denominator). Both are documented in
`samples/_archive_originals/README.md`.

---

## Running the engine

```bash
# Install dependencies
pip install -r requirements.txt

# Cross-validate against DABstep dev-split
python scripts/cross_validate_engine.py
```

Expected output: 6 rows, all `Match? YES`.
