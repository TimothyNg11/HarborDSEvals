# Linear regression of systolic blood pressure on age

You have access to an NHANES extract in `/data/` covering the August 2021 –
August 2023 cycle. The codebook for the extract is at
`/data/docs/messy_codebook.md`. **Read the codebook before doing anything
else** — column names have been changed from the original NCHS identifiers,
many missing-value sentinels are used, several decoy "weight" columns are
included, and a small number of obviously-erroneous rows have been
sprinkled in.

## Question

Fit a weighted linear regression of **systolic blood pressure** on:

- `age` (years; continuous),
- `male` (0/1 indicator for male sex),
- `bmi` (continuous, kg/m²),

using the **exam component** sample weight and restricting to adults aged
20 and older.

For each respondent, define systolic blood pressure as the mean of their
three available oscillometric readings (ignore missing readings).

Report the **coefficient on `age`** (in mm Hg per year of age), its
**design-adjusted standard error** (using the NHANES stratification and
PSU clustering), and the **95 % Wald confidence interval** for that
coefficient.

## Required output

Write your answer to `/output/result.json` in the following format:

```json
{
  "beta_age":  0.4026,
  "se_age":    0.0156,
  "ci_lower":  0.3720,
  "ci_upper":  0.4332
}
```

All four values are rounded to four decimal places. Units: mm Hg per year.

## Available files

- `/data/demo_messy.csv`            — primary demographic file
- `/data/demo_supplement.csv`       — supplementary demographic file
- `/data/bpx_messy.csv`             — three oscillometric BP readings
- `/data/bmx_messy.csv`             — body-mass index
- `/data/docs/messy_codebook.md`    — codebook (READ THIS)
- `/data/docs/nhanes_analytic_guidelines.md` — survey-design notes

## Notes

- The environment has no internet access.
- The CIs are for the **age** coefficient, not the prediction.
- A naive (non-design-adjusted) SE will significantly understate the true
  SE; the verifier checks for a CI consistent with proper PSU clustering.
- Records with missing/implausible age, BMI, or SBP must be dropped, and
  duplicates on `respondent_id` must be handled.
