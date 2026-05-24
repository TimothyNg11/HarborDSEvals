"""Convert clean NHANES/NHIS XPT/CSV files into AGGRESSIVELY messy CSVs.

What "aggressive" means:

1. ~12 % of numeric cells carry one of FIVE missing-value sentinels.
2. Renaming is non-obvious; the same semantic concept (e.g., sample weight)
   has many "wt_*" lookalikes, only ONE of which is correct per analysis.
3. Outlier rows are scattered through the data: ~5 % of rows have at least
   one nonsense value (BMI = 210, age = 999, etc.). They must be filtered.
4. Subtle type problems: ~3 % of numeric values are stored as strings with
   commas ("30,5" instead of "30.5") or include trailing units ("82 kg").
5. ~2 % of respondents appear as duplicates with slightly different data —
   agent must deduplicate on respondent_id.
6. Demographic information is split across TWO files (demo + demo_supplement)
   that must be joined on respondent_id; some respondents appear only in one
   file.
7. Many extra junk columns (timestamps, derived flags, etc.) that have no
   relevance and should be ignored.

The clean published answer is still recoverable when the agent reads the
codebook, joins both demographic files, deduplicates, drops outliers,
converts string sentinels to NaN, and selects the correct weight.
"""
from __future__ import annotations

import csv
import json
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import pyreadstat

CACHE = Path(__file__).resolve().parent.parent / "_data_cache"
OUT_ROOT = CACHE / "_messy"
OUT_ROOT.mkdir(exist_ok=True)

NHANES_RENAME = {
    "SEQN":     "respondent_id",
    "RIDAGEYR": "p_age_yr",
    "RIAGENDR": "p_sex_code",
    "RIDRETH3": "p_race_eth_v3",
    "RIDEXPRG": "p_pregnant_code",
    "DMDEDUC2": "p_education_max",
    "INDFMPIR": "p_pir_ratio",
    "DMDBORN4": "p_us_born",
    "BMXBMI":   "q_bmi_kgm2",
    "WTINT2YR": "wt_int_2yr",
    "WTMEC2YR": "wt_mec_2yr",
    "WTDRD1":   "wt_drd1",
    "SDMVSTRA": "design_stratum",
    "SDMVPSU":  "design_psu",
    "BPXOSY1":  "bp_osy_r1",
    "BPXOSY2":  "bp_osy_r2",
    "BPXOSY3":  "bp_osy_r3",
    "BPXODI1":  "bp_odi_r1",
    "BPXODI2":  "bp_odi_r2",
    "BPXODI3":  "bp_odi_r3",
    "DR1TKCAL": "d1_total_kcal",
    "DR1TSODI": "d1_total_sodium_mg",
    "DR1DRSTZ": "d1_recall_status",
}

NHIS_RENAME = {
    "AGEP_A":      "respondent_age",
    "WTFA_A":      "wt_sample_adult",
    "PAIFRQ3M_A":  "pain_freq_3mo",
    "PAIWKLM3M_A": "pain_work_limit_3mo",
    "PSTRAT":      "design_stratum",
    "PPSU":        "design_psu",
}

# Decoy weight column names (with plausible-but-fake values).
DECOY_WEIGHTS = [
    "wt_screener_2yr",
    "wt_household_2yr",
    "wt_subsample_a",
    "wt_subsample_b",
    "wt_panel_v1",
    "wt_panel_v2",
    "wt_calibration_raw",
    "wt_legacy_2018",
]

JUNK_COLS = [
    "ext_timestamp_capture",
    "internal_qa_flag",
    "deprecated_link_id",
    "supplement_batch_no",
    "freeform_notes_clipped",
    "v2_release_marker",
    "audit_trail_revision",
]

SENTINELS_NUM = ["", "NA", "REFUSED", "DK", "999.99", ".", "N/A"]
SENTINELS_INT = ["", "NA", "REFUSED", "DK", "9999", "."]


def _inject_missing(series: pd.Series, rng: np.random.Generator,
                    pool: list[str], frac: float) -> pd.Series:
    out = series.astype(object).copy()
    mask = rng.random(len(out)) < frac
    if not mask.any():
        return out
    choices = rng.integers(0, len(pool), size=int(mask.sum()))
    out.loc[mask] = [pool[i] for i in choices]
    return out


def _inject_string_typos(series: pd.Series, rng: np.random.Generator,
                         frac: float = 0.025) -> pd.Series:
    """Convert ~frac of numeric values to strings with commas or unit suffix."""
    out = series.astype(object).copy()
    mask = rng.random(len(out)) < frac
    if not mask.any():
        return out
    for idx in out.index[mask]:
        v = out.loc[idx]
        if pd.isna(v) or isinstance(v, str):
            continue
        # Choose: comma decimal, unit suffix, or leading sign error
        kind = rng.integers(0, 3)
        s = str(v)
        if kind == 0 and "." in s:
            out.loc[idx] = s.replace(".", ",")
        elif kind == 1:
            out.loc[idx] = f"{s} units"
        elif kind == 2:
            out.loc[idx] = f" {s} "  # leading/trailing whitespace
    return out


def _inject_outlier_rows(df: pd.DataFrame, n: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    last_id = int(pd.to_numeric(df["respondent_id"], errors="coerce").max())
    for i in range(n):
        row = {c: "" for c in df.columns}
        row["respondent_id"] = last_id + 1000 + i
        for c in df.columns:
            if c == "respondent_id":
                continue
            if pd.api.types.is_numeric_dtype(df[c]) or c.startswith(("wt_", "p_", "q_", "bp_", "d1_", "design_")):
                # Insert nonsense for numerical-ish columns
                pick = rng.integers(0, 6)
                if pick == 0:    row[c] = rng.choice([999, -1, 0, 9999])
                elif pick == 1:  row[c] = ""
                elif pick == 2:  row[c] = "REFUSED"
                elif pick == 3:  row[c] = rng.choice([210, -50, 5000])
                elif pick == 4:  row[c] = "DK"
                else:            row[c] = rng.normal()
        # Force at least one column to be clearly out of bounds
        if "p_age_yr" in df.columns and i % 3 == 0:
            row["p_age_yr"] = rng.choice([999, -3, 250])
        if "q_bmi_kgm2" in df.columns and i % 3 == 1:
            row["q_bmi_kgm2"] = rng.choice([210.0, -3.5, 999])
        rows.append(row)
    return pd.concat([df, pd.DataFrame(rows)], ignore_index=True)


def _inject_duplicates(df: pd.DataFrame, frac: float, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    n_dup = int(len(df) * frac)
    if n_dup == 0:
        return df
    dup_idx = rng.choice(len(df), size=n_dup, replace=False)
    dups = df.iloc[dup_idx].copy()
    # Slightly perturb one numeric column per duplicate so they aren't bitwise identical
    for c in df.columns:
        if c == "respondent_id":
            continue
        if pd.api.types.is_numeric_dtype(df[c]):
            dups[c] = dups[c] * (1 + rng.normal(0, 0.005, size=len(dups)))
            break
    return pd.concat([df, dups], ignore_index=True)


def _add_decoys_and_junk(df: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    # Decoy weights (only present for files that have a real weight)
    has_weight = any(c.startswith("wt_") for c in df.columns)
    if has_weight:
        for name in DECOY_WEIGHTS:
            if name not in df.columns:
                df[name] = np.round(rng.lognormal(9.5, 0.5, size=len(df)), 4)
    # Junk columns
    for name in JUNK_COLS:
        if name in df.columns:
            continue
        if "timestamp" in name:
            df[name] = pd.date_range("2021-08-01", periods=len(df), freq="h").strftime("%Y-%m-%dT%H:%M:%S")
        elif "flag" in name:
            df[name] = rng.choice(["YES", "NO", "PENDING"], size=len(df))
        elif "batch" in name or "revision" in name:
            df[name] = rng.integers(1, 50, size=len(df))
        else:
            df[name] = rng.choice(["", "a", "b", "c", "?", "—"], size=len(df))
    return df


def _shuffle_columns(df: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    cols = list(df.columns)
    # Keep respondent_id first; shuffle the rest
    rest = [c for c in cols if c != "respondent_id"]
    rng.shuffle(rest)
    return df[["respondent_id"] + rest]


def make_messy_nhanes(xpt: Path, out_csv: Path,
                      keep_cols: list[str], seed: int = 11,
                      missing_frac: float = 0.12,
                      outlier_n: int = 50,
                      typo_frac: float = 0.025,
                      dup_frac: float = 0.02) -> pd.DataFrame:
    df, _ = pyreadstat.read_xport(str(xpt), encoding="latin1")
    df = df[[c for c in keep_cols if c in df.columns]].copy()
    df = df.rename(columns={k: v for k, v in NHANES_RENAME.items() if k in df.columns})
    rng = np.random.default_rng(seed)

    df = _add_decoys_and_junk(df, rng)
    df = _inject_duplicates(df, dup_frac, seed)
    df = _inject_outlier_rows(df, outlier_n, seed + 1)

    # Inject sentinels and typos into "semantic" columns only
    semantic = [c for c in df.columns if c.startswith(("p_", "q_", "bp_", "d1_"))]
    for c in semantic:
        if pd.api.types.is_numeric_dtype(df[c]):
            df[c] = _inject_missing(df[c], rng, SENTINELS_NUM, missing_frac)
            df[c] = _inject_string_typos(df[c], rng, typo_frac)

    df = _shuffle_columns(df, rng)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_csv, index=False)
    print(f"  wrote {out_csv}  ({len(df)} rows x {len(df.columns)} cols)")
    return df


def make_split_demographics(seed: int = 7) -> None:
    """Split DEMO_L into two files: primary + supplement. Some respondents only
    in one file. Tasks must figure out the join."""
    xpt = CACHE / "NHANES_2021_2023" / "DEMO_L.xpt"
    df, _ = pyreadstat.read_xport(str(xpt), encoding="latin1")
    keep = ["SEQN", "RIDAGEYR", "RIAGENDR", "RIDRETH3", "RIDEXPRG",
            "DMDEDUC2", "INDFMPIR", "DMDBORN4",
            "WTINT2YR", "WTMEC2YR", "SDMVSTRA", "SDMVPSU"]
    df = df[[c for c in keep if c in df.columns]].copy()
    df = df.rename(columns={k: v for k, v in NHANES_RENAME.items() if k in df.columns})

    primary_cols = ["respondent_id", "p_age_yr", "p_sex_code", "p_race_eth_v3",
                    "p_pregnant_code", "design_stratum", "design_psu",
                    "wt_int_2yr", "wt_mec_2yr"]
    suppl_cols = ["respondent_id", "p_education_max", "p_pir_ratio", "p_us_born"]

    primary = df[primary_cols].copy()
    suppl = df[suppl_cols].copy()

    rng = np.random.default_rng(seed)
    primary = _add_decoys_and_junk(primary, rng)
    suppl = _add_decoys_and_junk(suppl, rng)

    primary = _inject_duplicates(primary, 0.02, seed)
    suppl   = _inject_duplicates(suppl,   0.015, seed + 1)
    primary = _inject_outlier_rows(primary, 40, seed + 2)
    suppl   = _inject_outlier_rows(suppl,   30, seed + 3)

    # Drop a random subset from the supplement file (so some respondents
    # appear only in primary).
    keep_mask = rng.random(len(suppl)) > 0.04
    suppl = suppl[keep_mask].copy()

    for d in (primary, suppl):
        for c in d.columns:
            if c.startswith(("p_", "q_")) and pd.api.types.is_numeric_dtype(d[c]):
                d[c] = _inject_missing(d[c], rng, SENTINELS_NUM, 0.12)
                d[c] = _inject_string_typos(d[c], rng, 0.025)

    primary = _shuffle_columns(primary, rng)
    suppl = _shuffle_columns(suppl, rng)

    primary.to_csv(OUT_ROOT / "demo_messy.csv", index=False)
    suppl.to_csv(OUT_ROOT / "demo_supplement.csv", index=False)
    print(f"  wrote demo_messy.csv ({len(primary)} rows)")
    print(f"  wrote demo_supplement.csv ({len(suppl)} rows)")


def make_messy_nhis() -> None:
    src = CACHE / "NHIS_2023" / "adult23csv.zip"
    out_csv = OUT_ROOT / "nhis_adult_messy.csv"
    with zipfile.ZipFile(src) as z:
        with z.open("adult23.csv") as f:
            df = pd.read_csv(f, low_memory=False)
    keep = list(NHIS_RENAME.keys())
    df = df[[c for c in keep if c in df.columns]].copy()
    df = df.rename(columns={k: v for k, v in NHIS_RENAME.items() if k in df.columns})

    # Add a respondent_id column for join semantics consistency.
    df.insert(0, "respondent_id", range(1, len(df) + 1))

    rng = np.random.default_rng(13)
    # Add decoy weights and junk
    for name in ["wt_screener", "wt_replicate_1", "wt_replicate_2",
                 "wt_panel_v1", "wt_legacy"]:
        df[name] = np.round(rng.lognormal(8.7, 0.5, size=len(df)), 4)
    for name in JUNK_COLS:
        if "timestamp" in name:
            df[name] = pd.date_range("2023-01-01", periods=len(df), freq="h").strftime("%Y-%m-%dT%H:%M:%S")
        else:
            df[name] = rng.choice(["", "x", "y", "?", "0"], size=len(df))

    df = _inject_duplicates(df, 0.02, 9)
    df = _inject_outlier_rows(df, 80, 21)
    for c in ("respondent_age", "pain_freq_3mo", "pain_work_limit_3mo"):
        if c in df.columns:
            df[c] = _inject_missing(df[c], rng, SENTINELS_NUM, 0.11)
            df[c] = _inject_string_typos(df[c], rng, 0.02)

    df = _shuffle_columns(df, rng)
    df.to_csv(out_csv, index=False)
    print(f"  wrote {out_csv}  ({len(df)} rows)")


def write_codebook(out_md: Path) -> None:
    text = """# NHANES extract — codebook (Aug 2021 – Aug 2023 cycle)

This codebook documents the columns in the CSV extracts shipped with this
task. Several columns have been renamed; the original NCHS variable name
is shown for reference but **the column name in the CSV is the one on the
left**.

> Warning: the extract intentionally contains real-world data-quality
> hazards — sentinel codes for missing values, duplicate respondents, and a
> small number of obviously-erroneous rows (e.g., `p_age_yr = 999`).
> Read the "Cleaning expectations" section at the bottom before any
> analysis.

## Files

- `demo_messy.csv`         — primary demographic file (one row per respondent_id)
- `demo_supplement.csv`    — supplementary demographic file (education, poverty, US-born). NOT every respondent_id in `demo_messy.csv` is present here.
- `bmx_messy.csv`          — body measurements (BMI)
- `bpx_messy.csv`          — blood-pressure readings
- `dr1tot_messy.csv`       — day-1 dietary recall totals

Files are joined on `respondent_id` (the original SEQN).

## Identifier and design variables

| Column            | Original | Description                                  |
|-------------------|----------|----------------------------------------------|
| `respondent_id`   | SEQN     | Person-level unique identifier (join key)    |
| `design_stratum`  | SDMVSTRA | Variance pseudo-stratum                      |
| `design_psu`      | SDMVPSU  | Variance pseudo-PSU                          |

## Demographics (split across `demo_messy.csv` + `demo_supplement.csv`)

| Column            | Original | Description                                                              | File          |
|-------------------|----------|--------------------------------------------------------------------------|---------------|
| `p_age_yr`        | RIDAGEYR | Age in years; 80 = "80 or older" topcode                                 | demo_messy    |
| `p_sex_code`      | RIAGENDR | 1 = male, 2 = female                                                     | demo_messy    |
| `p_race_eth_v3`   | RIDRETH3 | 1=Mex.Amer, 2=Other Hisp, 3=Non-Hisp White, 4=Non-Hisp Black, 6=Non-Hisp Asian, 7=Other/multi | demo_messy    |
| `p_pregnant_code` | RIDEXPRG | 1 = pregnant at exam, 2 = not pregnant, 3 = unknown                      | demo_messy    |
| `p_education_max` | DMDEDUC2 | 1=<9th, 2=9-11th, 3=HS/GED, 4=some college, 5=college+, 7/9=refused/DK   | **supplement**|
| `p_pir_ratio`     | INDFMPIR | Family income-to-poverty ratio (0.0–5.0 topcode at 5.0)                  | **supplement**|
| `p_us_born`       | DMDBORN4 | 1 = born in US, 2 = born elsewhere, 7/9 = refused/DK                     | **supplement**|

## Body measures

| Column         | Original | Description                                  | File      |
|----------------|----------|----------------------------------------------|-----------|
| `q_bmi_kgm2`   | BMXBMI   | Body Mass Index (kg/m^2)                     | bmx_messy |

## Blood pressure (oscillometric readings)

| Column       | Original | Description                       |
|--------------|----------|-----------------------------------|
| `bp_osy_r1`  | BPXOSY1  | Systolic, reading 1 (mm Hg)       |
| `bp_osy_r2`  | BPXOSY2  | Systolic, reading 2 (mm Hg)       |
| `bp_osy_r3`  | BPXOSY3  | Systolic, reading 3 (mm Hg)       |

## Dietary (day-1 24-hour recall)

| Column               | Original  | Description                                       |
|----------------------|-----------|---------------------------------------------------|
| `d1_total_kcal`      | DR1TKCAL  | Total energy intake (kcal)                        |
| `d1_total_sodium_mg` | DR1TSODI  | Total sodium intake (mg)                          |
| `d1_recall_status`   | DR1DRSTZ  | 1 = reliable, 2 = unreliable, 4 = reported but uncodeable, 5 = not done |

## Sample weights — CRITICAL

There are **many** weight columns. Most are decoys retained from internal
processing and are NOT valid for analysis. Only the three columns below are
real NHANES sample weights:

| Column            | Original  | Use for                                                  |
|-------------------|-----------|----------------------------------------------------------|
| `wt_int_2yr`      | WTINT2YR  | Interview-only (questionnaire) analyses                  |
| `wt_mec_2yr`      | WTMEC2YR  | Mobile Examination Center (MEC) analyses — BMI, BP, lab  |
| `wt_drd1`         | WTDRD1    | Dietary day-1 (24-hour recall) analyses                  |

All other columns starting with `wt_` (`wt_screener_2yr`, `wt_household_2yr`,
`wt_subsample_a`/`_b`, `wt_panel_v1`/`_v2`, `wt_calibration_raw`,
`wt_legacy_2018`, …) are decoys and must be ignored. Records with
weight = 0 should be excluded **from the chosen weight column only**.

## Missing-value sentinels

The CSVs use a mix of missing-value sentinels (legacy from upstream
processing). Treat ALL of these as missing:

- Empty cell (blank)
- `NA`, `N/A`
- `REFUSED`
- `DK` (don't know)
- `.` (single dot)
- `999.99` and the integer `9999`
- For categorical codes: `7` = refused, `9` = don't know

Some numeric cells were stored as strings (e.g., `"30,5"` with a comma
decimal separator, or `"82 units"` with a trailing word) due to upstream
data-entry quirks. Cast such values to numeric defensively.

## Cleaning expectations

Before any weighted analysis, you should:

1. Read both demographic files and join them on `respondent_id`. Keep
   respondents who appear in at least one file (left join from
   `demo_messy.csv` if the analysis only needs primary demographics).
2. Deduplicate on `respondent_id` (some respondents appear more than once).
3. Convert all sentinel strings to NaN and cast numeric columns to numeric.
4. Drop respondents with implausible age (`< 0` or `> 100`), implausible
   BMI (`< 8` or `> 100`), or non-positive weight in the chosen weight
   column.
5. Apply analysis-specific filters (age range, sex, valid response, etc.).
6. Select the sample weight appropriate to your analysis.

A small number of intentionally-corrupted rows (e.g., `p_age_yr = 999`,
`q_bmi_kgm2 = 210`) are present. Step 4 should remove them.
"""
    out_md.write_text(text, encoding="utf-8")
    print(f"  wrote {out_md}")


def main():
    make_split_demographics()
    make_messy_nhanes(
        CACHE / "NHANES_2021_2023" / "BMX_L.xpt",
        OUT_ROOT / "bmx_messy.csv",
        keep_cols=["SEQN", "BMXBMI"],
        seed=23,
    )
    make_messy_nhanes(
        CACHE / "NHANES_2021_2023" / "BPX_L.xpt",
        OUT_ROOT / "bpx_messy.csv",
        keep_cols=["SEQN", "BPXOSY1", "BPXOSY2", "BPXOSY3", "BPXODI1", "BPXODI2", "BPXODI3"],
        seed=29,
    )
    make_messy_nhanes(
        CACHE / "NHANES_2021_2023" / "DR1TOT_L.xpt",
        OUT_ROOT / "dr1tot_messy.csv",
        keep_cols=["SEQN", "DR1TKCAL", "DR1TSODI", "WTDRD1", "DR1DRSTZ"],
        seed=31,
    )
    make_messy_nhis()
    write_codebook(OUT_ROOT / "messy_codebook.md")


if __name__ == "__main__":
    main()
