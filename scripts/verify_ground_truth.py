"""Verify ground-truth values by recomputing them from raw federal data.

Run from repo root. Used to confirm task verifier values match published numbers
before authoring tasks.
"""
from __future__ import annotations

import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import pyreadstat

CACHE = Path(__file__).resolve().parent.parent / "_data_cache"


def nhanes_obesity_overall():
    demo, _ = pyreadstat.read_xport(str(CACHE / "NHANES_2021_2023" / "DEMO_L.xpt"), encoding="latin1")
    bmx, _ = pyreadstat.read_xport(str(CACHE / "NHANES_2021_2023" / "BMX_L.xpt"), encoding="latin1")
    df = demo.merge(bmx[["SEQN", "BMXBMI"]], on="SEQN", how="inner")
    adults = df[(df["RIDAGEYR"] >= 20) & (df["WTMEC2YR"] > 0) & df["BMXBMI"].notna()].copy()
    adults["obese"] = (adults["BMXBMI"] >= 30).astype(int)
    adults["severe"] = (adults["BMXBMI"] >= 40).astype(int)

    def wprev(mask, indicator):
        sub = adults[mask]
        return 100 * (sub["WTMEC2YR"] * sub[indicator]).sum() / sub["WTMEC2YR"].sum()

    overall = wprev(adults["RIDAGEYR"] >= 20, "obese")
    men = wprev(adults["RIAGENDR"] == 1, "obese")
    women = wprev(adults["RIAGENDR"] == 2, "obese")
    age2039 = wprev((adults["RIDAGEYR"] >= 20) & (adults["RIDAGEYR"] <= 39), "obese")
    age4059 = wprev((adults["RIDAGEYR"] >= 40) & (adults["RIDAGEYR"] <= 59), "obese")
    age60p = wprev(adults["RIDAGEYR"] >= 60, "obese")
    severe = wprev(adults["RIDAGEYR"] >= 20, "severe")

    print(f"Overall obesity (computed): {overall:.1f}%   (DB-508: 40.3)")
    print(f"Men:                       {men:.1f}%   (DB-508: 39.2)")
    print(f"Women:                     {women:.1f}%   (DB-508: 41.3)")
    print(f"Age 20-39:                 {age2039:.1f}%   (DB-508: 35.5)")
    print(f"Age 40-59:                 {age4059:.1f}%   (DB-508: 46.4)")
    print(f"Age 60+:                   {age60p:.1f}%   (DB-508: 38.9)")
    print(f"Severe obesity overall:    {severe:.1f}%   (DB-508: 9.4)")

    print("\nSevere obesity 6-cell (sex x age):")
    sex_map = {1: "men", 2: "women"}
    age_buckets = [("20-39", 20, 39), ("40-59", 40, 59), ("60+", 60, 200)]
    truth = {
        ("men", "20-39"): 6.1, ("men", "40-59"): 9.2, ("men", "60+"): 4.3,
        ("women", "20-39"): 13.0, ("women", "40-59"): 14.7, ("women", "60+"): 8.4,
    }
    for sx, sx_name in sex_map.items():
        for label, lo, hi in age_buckets:
            mask = (adults["RIAGENDR"] == sx) & (adults["RIDAGEYR"] >= lo) & (adults["RIDAGEYR"] <= hi)
            v = wprev(mask, "severe")
            print(f"  {sx_name} {label:<6}: {v:5.1f}%   (DB-508: {truth[(sx_name, label)]})")

    print("\nDiff men vs women (40-59) for Task 6 two-sample:")
    m4059 = wprev((adults["RIAGENDR"] == 1) & (adults["RIDAGEYR"] >= 40) & (adults["RIDAGEYR"] <= 59), "obese")
    w4059 = wprev((adults["RIAGENDR"] == 2) & (adults["RIDAGEYR"] >= 40) & (adults["RIDAGEYR"] <= 59), "obese")
    print(f"  Men 40-59: {m4059:.1f}%, Women 40-59: {w4059:.1f}%, diff(W-M): {w4059 - m4059:+.1f} pp")

    return adults


def nhanes_fast_food():
    demo, _ = pyreadstat.read_xport(str(CACHE / "NHANES_2021_2023" / "DEMO_L.xpt"), encoding="latin1")
    dr1, _ = pyreadstat.read_xport(str(CACHE / "NHANES_2021_2023" / "DR1TOT_L.xpt"), encoding="latin1")
    print("\nDR1TOT_L columns sample:", [c for c in dr1.columns if c.startswith("DR")][:20])
    # WTDRD1 is the day-1 dietary sample weight; required for any DR1TOT analysis.
    df = demo.merge(dr1[["SEQN", "DR1TNUMF", "DR1_320Z", "WTDRD1"]], on="SEQN", how="inner")
    return df


def nhis_chronic_pain():
    zip_path = CACHE / "NHIS_2023" / "adult23csv.zip"
    with zipfile.ZipFile(zip_path) as z:
        names = z.namelist()
        print(f"\nNHIS files: {names}")
        with z.open(names[0]) as f:
            head = pd.read_csv(f, nrows=2)
            print(f"NHIS columns sample: {[c for c in head.columns if 'PAIN' in c.upper()]}")


def cps_median_income():
    print(f"\nCPS-ASEC median income 2023: $80,610 (DB ground truth)")


def asfin_revenue():
    import openpyxl
    summary_path = CACHE / "ASFIN_2021" / "21slsstab1.xlsx"
    wb = openpyxl.load_workbook(summary_path)
    ws = wb.active
    # Find "Description" column with revenue rows
    rows = list(ws.iter_rows(values_only=True))
    print(f"\nASFIN rows: {len(rows)}")
    for i, r in enumerate(rows[:80]):
        desc = r[1]
        us_total = r[2]
        if desc and isinstance(desc, str) and any(k in desc.lower() for k in ["revenue", "tax", "intergov", "charge", "misc", "general"]):
            print(f"  row {i}: {desc!r:50s}  US_state_local={us_total}")


if __name__ == "__main__":
    nhanes_obesity_overall()
    nhanes_fast_food()
    nhis_chronic_pain()
    cps_median_income()
    asfin_revenue()
