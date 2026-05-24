# Obesity prevalence in a four-condition NHANES subgroup with Wilson CI

You have access to a NHANES extract in `/data/` covering the August 2021 –
August 2023 cycle. The codebook for the extract is at
`/data/docs/messy_codebook.md`.

**Read the codebook first.** Column names have been changed from the
original NCHS identifiers, the CSVs contain a mix of missing-value
sentinels, several decoy weight columns are present, and a small number
of obviously-erroneous rows have been sprinkled in.

## Question

Compute the prevalence of obesity (BMI ≥ 30 kg/m²) among adults
satisfying ALL FOUR of the following conditions:

1. Non-Hispanic Asian (RIDRETH3 = 6, documented as `p_race_eth_v3`),
2. Female,
3. Age 50–69 inclusive,
4. Born outside the United States (`p_us_born` = 2, original `DMDBORN4`).

Use the appropriate sample weight for examination-component analyses
(BMI is a physical exam measurement).

In addition, compute the **Wilson score 95 % confidence interval** for
this prevalence using the WEIGHTED sample-size-correction form
(Korn–Graubard / Wilson on the design-effective sample size). Use the
NHANES design effect computed via Taylor linearization as

    DEFF  =  Var_design(p) / Var_binomial(p)
    n_eff =  n_raw / DEFF

Then apply the Wilson score formula to the weighted prevalence with the
effective sample size:

    center = (n_eff * p + z²/2) / (n_eff + z²)
    half   =  z * sqrt( (n_eff * p (1 - p) + z²/4) / (n_eff + z²)² )
    CI     = center ± half

with `z = 1.96`. Report `lower`, `upper` as percentages.

## Required output

Write your answer to `/output/result.json`:

```json
{
  "prevalence": 8.10,
  "ci_lower":   1.50,
  "ci_upper":   34.65
}
```

All three values are percentages, rounded to two decimal places.

## Available files

- `/data/demo_messy.csv`            — primary demographic file
- `/data/demo_supplement.csv`       — supplementary demographic file
   (includes `p_us_born`)
- `/data/bmx_messy.csv`             — body-measures (BMI)
- `/data/docs/messy_codebook.md`    — codebook (READ THIS)

## Notes

- Output percentages, not proportions.
- The environment has no internet access.
- "Inclusive" age bounds: include integers 50–69.
- The sample within these four conditions is very small (n unweighted
  is on the order of 30–40). The Wilson score CI on the effective sample
  size is necessary BECAUSE the binomial-style and the normal-approxi-
  mation CIs are unreliable at this n. Submitting a naive
  binomial-CI or symmetric Wald CI will fall outside the verifier's
  acceptance band.
