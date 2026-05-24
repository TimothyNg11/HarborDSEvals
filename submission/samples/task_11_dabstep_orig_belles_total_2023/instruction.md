# Total fees paid by Belles_cookbook_store in 2023

This task uses the DABstep payment-processing dataset and manual in `/data/`.
The fee-matching semantics is the standard one described in section 5 of
`/data/manual.md`: a rule applies to a transaction iff every non-null rule
field matches the transaction (empty list / null is "any").

For each transaction, the fee charged is the **sum** of
`fixed_amount + rate * eur_amount / 10000` across **every** matching fee
rule. (Some hard DABstep tasks use exactly this semantics, e.g. the
dev-split list-of-applicable-fee-IDs questions.)

## Question

What is the total fees (in EUR) that Belles_cookbook_store paid across
**all of 2023**, summed across every matching fee rule per transaction?

## Required output

Write a single non-negative number, rounded to **4 decimal places**, to
`/output/answer.txt`. Example format: `3914.3621`

## Notes

- The environment has no internet access.
- All data live in `/data/`: `payments.csv`, `fees.json`,
  `merchant_data.json`, `merchant_category_codes.csv`,
  `acquirer_countries.csv`, `manual.md`, `payments-readme.md`.
- Belles_cookbook_store has 13,848 transactions in 2023; expect non-trivial
  computation.
