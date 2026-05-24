# State vs local share of tax revenue (US, 2021)

You have access to the Census Bureau's 2021 Annual Survey of State and
Local Government Finances (ASLGF) summary table in
`/data/21slsstab1.xlsx`, with two reference PDFs in `/data/docs/`.

## Question

For the United States in 2021, of total **tax revenue** raised by state and
local governments **combined**, what percentage was raised by:

1. **State** governments, and
2. **Local** governments

individually?

## Required output

Write your answer to `/output/result.json` in the following format:

```json
{
  "state_share":  60.03,
  "local_share":  39.97
}
```

Values are percentages of US-total state-and-local tax revenue, rounded to
two decimal places. They must sum to 100.

## Available files

- `/data/21slsstab1.xlsx` — full state-by-state ASLGF summary table
- `/data/docs/2021alfinsummarybrief.pdf` — Census summary brief
- `/data/docs/2021_methodology.pdf` — methodology notes

## Notes

- The spreadsheet has hundreds of columns. Within each state's block, the
  columns are: state+local combined, then state-only, then local-only.
- The "Taxes" row sits inside the General Revenue block.
- The environment has no internet access.
