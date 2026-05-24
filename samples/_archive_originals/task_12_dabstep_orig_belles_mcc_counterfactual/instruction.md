# Counterfactual fee delta when Belles_cookbook_store reclassifies MCC

This task uses the DABstep payment-processing dataset and manual in `/data/`.
The fee-matching semantics is the standard one in section 5 of
`/data/manual.md`: a rule applies iff every non-null field matches; the fee
per transaction is the **sum** across every matching rule.

Belles_cookbook_store currently has `merchant_category_code = 7997`
(per `/data/merchant_data.json`). Suppose Belles reclassifies its MCC to
`5411` (Grocery Stores, Supermarkets), keeping every other merchant
attribute unchanged.

## Question

What is the resulting **delta in total 2023 fees** (new total minus old
total), in EUR? A positive number means Belles pays MORE under the new
MCC; negative means LESS.

## Required output

Write a single signed number, rounded to **6 decimal places**, to
`/output/answer.txt`. Example format: `+1234.567890` or `-1234.567890`
(the leading sign is optional for positive numbers).

## Notes

- The environment has no internet access.
- All data live in `/data/`. The merchant file shows current MCC; for
  this task, mutate Belles's MCC only.
- The same fee-rule-matching code that computes the original-MCC total
  fees can be re-run with `5411` swapped in.
