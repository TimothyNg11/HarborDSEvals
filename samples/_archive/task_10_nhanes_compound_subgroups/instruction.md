# Erreygers concentration index of SEVERE obesity by family income

You have access to an NHANES extract in `/data/` covering the August 2021 –
August 2023 cycle. The codebook is at `/data/docs/messy_codebook.md`.

**Read the codebook before doing anything else.** Column names have been
changed, the CSVs contain a mix of missing-value sentinels, several decoy
weight columns are present, and a small number of obviously-erroneous rows
are sprinkled in.

## Background

For a *bounded* binary outcome, the **standard** Wagstaff concentration
index has known scaling problems: its range depends on the outcome
prevalence, so it is not comparable across outcomes with different mean
levels. Erreygers (2009, *Journal of Health Economics* 28(2), 504–515)
introduced the corrected index

    E = 4 * μ_y * (1 - μ_y) * C

where:

- `μ_y` is the weighted mean of the binary outcome,
- `C` is the standard concentration index of the binary outcome over the
  socio-economic ranking variable.

The Erreygers index `E` is bounded in `[-1, 1]` and is the formula
required for this task. **Do not report the unadjusted Wagstaff or
Kakwani-style index.**

For the standard `C`, use the algebraic identity:

    C = 2 * Σ_i ( w_i * y_i * R_i ) / ( W * μ_y )  -  1

where `w_i` is the respondent's NHANES weight, `R_i` is the fractional
rank of the respondent in the weighted population distribution of the SES
variable (midpoint of cumulative weight share), `W = Σ_i w_i`, and
`μ_y = Σ_i w_i y_i / W`.

## Question

Compute the **Erreygers concentration index** of **severe obesity** (BMI
≥ 40 kg/m²) over **family income-to-poverty ratio** (`p_pir_ratio`), for
U.S. adults age 20 and older, using the appropriate NHANES sample weight
for examination analyses.

Note that severe obesity (BMI ≥ 40), **not** obesity (BMI ≥ 30), is the
outcome here. The two indices differ markedly because severe obesity has
a much lower prevalence and therefore a much smaller Erreygers correction
factor `4 * μ_y * (1 - μ_y)`.

## Required output

Write your answer to `/output/result.txt` as a single signed number,
rounded to **four** decimal places. Example format: `-0.0420`

## Available files

- `/data/demo_messy.csv`            — primary demographic file
- `/data/demo_supplement.csv`       — supplementary demographic file
   (includes `p_pir_ratio`)
- `/data/bmx_messy.csv`             — body mass index
- `/data/docs/messy_codebook.md`    — codebook

## Notes

- The environment has no internet access.
- Drop respondents whose `p_pir_ratio` is missing.
- The Erreygers index for severe obesity is roughly an order of magnitude
  smaller than its standard-`C` counterpart in this sample because the
  prevalence of severe obesity is far from 0.5.
- Submitting the standard `C` value (rather than `E`) will fail the
  verifier by a wide margin.
