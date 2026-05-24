# Card scheme with the lowest average per-transaction fee

This task uses the DABstep payment-processing dataset and manual in `/data/`.
The fee-matching semantics is the standard one in section 5 of
`/data/manual.md`: a rule applies iff every non-null field matches; the fee
per transaction is the **sum** across every matching rule.

Compute the **average per-transaction fee** (in EUR) for each card scheme
present in `payments.csv` (GlobalCard, NexPay, SwiftCharge, TransactPlus)
across **all 2023 transactions**.

## Question

Which card scheme has the LOWEST average per-transaction fee, and what
is that average?

## Required output

Write your answer to `/output/answer.txt` in the format
`scheme_name:average_fee` where `average_fee` is rounded to 6 decimal
places. Example format: `NexPay:0.043202`. No extra prose; no trailing
units.

## Notes

- The environment has no internet access.
- Per-transaction fee = sum across every matching rule (a transaction
  may match many rules; many transactions match zero rules and contribute
  a fee of 0 EUR).
- The average is over all transactions for that scheme (including
  zero-fee transactions).
