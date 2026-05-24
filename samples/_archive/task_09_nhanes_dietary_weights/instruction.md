# Weighted median absolute deviation of sodium intake (adult women)

You have access to a NHANES extract in `/data/` covering the August 2021 –
August 2023 cycle. The codebook is at `/data/docs/messy_codebook.md`.

**Read the codebook before doing anything else.** Column names have been
changed from the original NCHS identifiers, the CSVs contain a mix of
missing-value sentinels, several decoy weight columns are present, and a
small number of obviously-erroneous rows have been sprinkled in.

## Background — weighted MAD around the weighted median

The **weighted Median Absolute Deviation around the weighted median**
(`wMAD`) is the canonical robust dispersion measure for skewed,
weighted distributions:

```
m   = weighted_median(x_i, w_i)
d_i = |x_i - m|
wMAD = weighted_median(d_i, w_i)
```

where `weighted_median` is the linearly-interpolated weighted quantile
at probability 0.5 (Hyndman-Fan type 4 / classical weighted quantile):
sort by the relevant variable, accumulate weights, find the two values
bracketing cumulative weight = 0.5 × total weight, and interpolate.

The wMAD is NOT the same as the unweighted `numpy.median(abs(x - median(x)))`;
applying the weighted median twice (once for the centre, once for the
dispersion) is essential.

## Question

Among U.S. adult women (age ≥ 20) with a **reliable** day-1 dietary
recall, compute the **weighted Median Absolute Deviation (wMAD)** of
total daily sodium intake (mg).

Use the appropriate sample weight for day-1 dietary recall analyses
(NOT the exam weight).

## Required output

Write your answer to `/output/result.txt` as a single number in
milligrams, rounded to one decimal place. Example format: `980.3`

## Available files

- `/data/demo_messy.csv`            — primary demographic file
- `/data/demo_supplement.csv`       — supplementary demographic file
- `/data/dr1tot_messy.csv`          — day-1 dietary recall totals
- `/data/docs/messy_codebook.md`    — codebook (READ THIS)
- `/data/docs/dietary_methodology.png` — methodology screenshot

## Notes

- The environment has no internet access.
- The wMAD requires TWO weighted median computations (one for the centre
  `m`, one for the median of `|x - m|`).
- The unweighted MAD (`scipy.stats.median_abs_deviation`) will give a
  noticeably different value because the weights matter.
- The wMAD of the *unweighted* deviations would also be wrong.
