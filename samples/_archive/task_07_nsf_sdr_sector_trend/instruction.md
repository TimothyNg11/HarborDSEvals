# Computer-sciences share of industry-employed doctorate-holders

You have access to NSF SDR 2023 Table 12-1 in `/data/nsf25321-tab012-001.xlsx`
and a figure that defines NCSES's three-way sector categorization in
`/data/figure_sector_categories.png`.

## Question

Using the **"industry"** sector as defined in the figure (i.e., the rollup
of the detailed sector columns the figure assigns to "industry"), compute
the share of **industry-employed** doctorate-holders whose field of doctorate
is **Computer and information sciences**.

That is:

    100 * (CS doctorates employed in industry)
        / (all doctorates employed in industry)

Use the "All fields" total *only* for sanity, not as the denominator. The
correct denominator is the industry-employed total across all fields.

## Required output

Write your answer to `/output/result.txt` as a single number — the share in
percent, rounded to two decimal places. Example format: `5.44`

## Available files

- `/data/nsf25321-tab012-001.xlsx`        — Table 12-1
- `/data/figure_sector_categories.png`    — defines the 3-way categorization

## Notes

- The spreadsheet is wide and has multi-line headers; identify columns by
  their text labels, not by hard-coded position.
- "Computer and information sciences" is one row of the spreadsheet.
- The environment has no internet access.
