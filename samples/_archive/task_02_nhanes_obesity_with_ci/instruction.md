# Age-standardized obesity prevalence by education

You have access to a NHANES extract in `/data/` covering the August 2021 –
August 2023 cycle. The codebook is at `/data/docs/messy_codebook.md`.

**Read the codebook first.** Column names have been changed, several decoy
"weight" columns are present, and the CSV uses multiple missing-value
sentinels.

## Background

NCHS reports **age-standardized** prevalences by computing the
weighted prevalence within each pre-specified age band and then taking a
weighted average of those band-specific rates using the **Year-2000 U.S.
Standard Population**. The standardized rate "removes" differences in age
distribution between subgroups so that comparisons are meaningful.

For this task, use the three-band Year-2000 standard population weights
shown below (renormalized to sum to 1.0):

| Age band | Standard population (counts) | Weight   |
|----------|------------------------------|----------|
| 20-39    | 76,185,176                   | 0.385      |
| 40-59    | 70,391,460                   | 0.356      |
| 60+      | 51,138,334                   | 0.259      |

(The standard weights are derived from the 2000 Census standard
population, restricted to ages 20+ and renormalised; use the EXACT counts
above when computing your weights, then standardise.)

## Question

Among U.S. adults age **25 and older** with a valid education response
(1-5 on the original `DMDEDUC2` scale; documented in the codebook as
`p_education_max`), compute the **age-standardized obesity prevalence
(BMI ≥ 30)** separately for:

1. Adults with **high-school graduate or less** (`p_education_max` in
   {1, 2, 3}), and
2. Adults with **at least some college education** (`p_education_max` in
   {4, 5}).

Then report the rate **difference** (low minus high), in percentage points.

## Required output

Write your answer to `/output/result.json` in the following format:

```json
{
  "low_ed_std_prev":  47.01,
  "high_ed_std_prev": 39.22,
  "rate_difference":   7.78
}
```

All three values are percentages or percentage-point differences,
rounded to two decimal places.

## Available files

- `/data/demo_messy.csv`            — primary demographic file
- `/data/demo_supplement.csv`       — supplementary demographic file
   (includes `p_education_max`)
- `/data/bmx_messy.csv`             — body mass index
- `/data/docs/messy_codebook.md`    — codebook

## Notes

- The environment has no internet access.
- The crude (unstandardized) prevalence is NOT acceptable here. You must
  apply the Year-2000 weights to age-band-specific prevalences.
- The education variable lives in the **supplementary** demographic file;
  join both demographic files on `respondent_id`.
