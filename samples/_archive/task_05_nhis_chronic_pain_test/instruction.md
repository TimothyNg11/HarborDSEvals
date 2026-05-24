# Population Attributable Fraction of high-impact pain by age (NHIS)

You have access to the 2023 NHIS Sample Adult interview file in
`/data/nhis_adult_messy.csv`. The codebook is at
`/data/docs/messy_codebook.md`. The chronic-pain documentation is at
`/data/docs/PAI_documentation.md`.

**Read both docs first.** Column names differ from the original NHIS
identifiers, several decoy weight columns are present, and the CSV uses
multiple missing-value sentinels plus a handful of obviously-erroneous
rows.

## Definitions

- **Chronic pain**: `pain_freq_3mo` ∈ {3, 4}.
- **High-impact pain**: `pain_work_limit_3mo` ∈ {3, 4}.
- "Older": age ≥ 65; "Younger": age 18-44 (inclusive).

Compute over Sample Adults with chronic pain AND valid (1-4) response to
`pain_work_limit_3mo`. Drop adults age 45-64 from the analysis.

## Background — Population Attributable Fraction

Among chronic-pain adults, fit a survey-weighted logistic regression of
high-impact pain on a single binary exposure `age65plus`:

    logit P(high_impact = 1)  =  β_0  +  β_1 * age65plus

The **population attributable fraction (PAF)** of high-impact pain due
to being aged 65+ is given by Levin's formula expressed in terms of the
odds ratio and the prevalence of the exposure **among cases**
(the so-called Miettinen–Bruzzi PAF, the form preferred by NCHS for
case-control style analyses):

    PAF  =  P(exposed | case)  *  ( OR - 1 ) / OR

where `OR = exp(β_1)` is the design-adjusted odds ratio, and
`P(exposed | case)` is the weighted prevalence of `age65plus = 1` among
respondents who reported high-impact pain.

## Question

Among NHIS Sample Adults with chronic pain (and a valid
`pain_work_limit_3mo` response), comparing adults age ≥ 65 against
adults age 18-44 (inclusive), compute:

1. The design-adjusted odds ratio (OR) from the logistic regression
   described above, with Taylor-sandwich standard error clustered on
   `design_psu` within `design_stratum`.
2. The Miettinen–Bruzzi PAF as defined above (as a proportion in [0, 1],
   not a percentage).

## Required output

Write your answer to `/output/result.json` in the following format:

```json
{
  "odds_ratio": 1.70,
  "paf":        0.27
}
```

- `odds_ratio` rounded to two decimal places.
- `paf` rounded to two decimal places (proportion, not percentage).

## Available files

- `/data/nhis_adult_messy.csv`        — Sample Adult file (CSV)
- `/data/docs/messy_codebook.md`      — codebook for the NHIS extract
- `/data/docs/PAI_documentation.md`   — chronic-pain question
                                        documentation

## Notes

- The environment has no internet access.
- Use a survey-weighted logistic regression (weights = `wt_sample_adult`)
  with a Taylor sandwich SE clustered on `design_psu` within
  `design_stratum` for the OR.
- The expected PAF is positive (older adults with chronic pain are MORE
  likely to have high-impact pain, so being 65+ "explains" a positive
  share of cases).
