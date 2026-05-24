# Standard deviation of Crossfit_Hanna's monthly fees in 2023

This task uses the DABstep payment-processing dataset and manual in `/data/`.
The fee-matching semantics is the standard one in section 5 of
`/data/manual.md`: a rule applies iff every non-null field matches; the fee
per transaction is the **sum** across every matching rule.

For Crossfit_Hanna in 2023, compute the **per-transaction fee** for every
one of their transactions, group those fees by **calendar month** (using
`day_of_year` mapped to a 2023 calendar — i.e. day 1 = Jan 1, day 32 =
Feb 1, accounting for the fact that 2023 is not a leap year), sum within
each month to get a series of 12 monthly totals, then compute the
**sample standard deviation** of those 12 monthly totals with the
Bessel-corrected denominator `n - 1` (ddof = 1).

## Question

What is the sample standard deviation (ddof = 1) of Crossfit_Hanna's
12 monthly fee totals for 2023, in EUR?

## Required output

Write a single non-negative number, rounded to **6 decimal places**, to
`/output/answer.txt`. Example format: `80.329334`

## Notes

- The environment has no internet access.
- Use the population-of-12 (Jan–Dec 2023) and sample SD (ddof = 1). The
  population SD (ddof = 0) differs and will fail the verifier.
- The fee for a transaction is the sum across every matching rule.
