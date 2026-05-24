# Age-standardized obesity rate ratio (Black vs White women)

You have access to a NHANES extract in `/data/` covering the August 2021 –
August 2023 cycle. The codebook is at `/data/docs/messy_codebook.md`.

**Read the codebook first.** Column names have been changed and several
decoy "weight" columns are present.

## Background

The **age-standardized rate ratio** is the standard NCHS way to compare a
binary outcome between two subgroups after removing age-composition
differences. Use the Year-2000 U.S. Standard Population weights (3-band,
age 20+), with the EXACT counts shown below:

| Age band | Standard population counts | Renormalized weight |
|----------|----------------------------|---------------------|
| 20-39    | 76,185,176                 | 0.385                 |
| 40-59    | 70,391,460                 | 0.356                 |
| 60+      | 51,138,334                 | 0.259                 |

Within each subgroup, compute the weighted prevalence in each age band,
then take a weighted average using those standard weights. The rate ratio
is the standardized rate in the numerator subgroup divided by the
standardized rate in the denominator subgroup.

## Question

Among U.S. adult women (age ≥ 20, `p_sex_code = 2`), compute:

1. The age-standardized obesity prevalence (BMI ≥ 30) among **non-Hispanic
   Black** women (`p_race_eth_v3 = 4`).
2. The age-standardized obesity prevalence among **non-Hispanic White**
   women (`p_race_eth_v3 = 3`).
3. The **rate ratio** of NHB to NHW age-standardized obesity prevalence
   (numerator / denominator).

## Required output

Write your answer to `/output/result.json` in the following format:

```json
{
  "nhb_std_prev": 55.03,
  "nhw_std_prev": 40.35,
  "rate_ratio":    1.3638
}
```

- Prevalences are percentages, rounded to two decimal places.
- `rate_ratio` is rounded to **four** decimal places.

## Available files

- `/data/demo_messy.csv`            — primary demographic file
- `/data/bmx_messy.csv`             — body mass index
- `/data/docs/messy_codebook.md`    — codebook

## Notes

- The environment has no internet access.
- The crude (unstandardized) rate ratio is NOT acceptable.
- Drop respondents with missing or implausible age, BMI, or non-positive
  exam weight.
