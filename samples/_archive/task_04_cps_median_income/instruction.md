# Race income ratio from CPS-ASEC Table A-1

You have access to the Census Bureau's Current Population Survey Annual
Social and Economic Supplement (CPS-ASEC) **Table A-1** for the 2024 release
(reporting 2022 and 2023 income) in `/data/tableA1.xlsx`.

## Question

For 2023, compute the ratio of **Asian** household median income to **non-
Hispanic White** household median income, expressed as a percentage.

That is:  `100 * median_income(Asian) / median_income(White, not Hispanic)`.

Use the **2023** column (not 2022).

## Required output

Write your answer to `/output/result.txt` as a single number — the ratio in
percent, rounded to two decimal places. Example format: `126.67`

## Available files

- `/data/tableA1.xlsx` — the Census P60-282 Table A-1 spreadsheet

## Notes

- Both numerator and denominator are published in this same table.
- "Non-Hispanic White" and "White" appear as separate rows; only one of them
  is the correct denominator here.
- Use 2023 dollars throughout (Census has already inflation-adjusted both
  years to 2023 dollars).
- The environment has no internet access.
