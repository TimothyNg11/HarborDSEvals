"""Compute ground truth for the hardened task suite. None of these answers
appear in standard NCHS Data Briefs, so frontier models cannot fall back on
memorisation.
"""
from __future__ import annotations

import json
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import pyreadstat
import scipy.stats as ss

CACHE = Path(__file__).resolve().parent.parent / "_data_cache"


def _design_se_prev(d: pd.DataFrame, ycol: str, wcol: str,
                    strat: str = "SDMVSTRA", psu: str = "SDMVPSU") -> tuple[float, float]:
    """Taylor-linearization (prev, SE) for a 0/1 indicator in a complex survey."""
    wsum = d[wcol].sum()
    p = (d[wcol] * d[ycol]).sum() / wsum
    d = d.copy()
    d["__z"] = d[wcol] * (d[ycol] - p) / wsum
    var = 0.0
    for _, g in d.groupby(strat):
        psu_sums = g.groupby(psu)["__z"].sum()
        m = len(psu_sums)
        if m <= 1:
            continue
        var += m / (m - 1) * ((psu_sums - psu_sums.mean()) ** 2).sum()
    return float(p), float(np.sqrt(var))


def _design_se_mean(d: pd.DataFrame, ycol: str, wcol: str,
                    strat: str = "SDMVSTRA", psu: str = "SDMVPSU") -> tuple[float, float]:
    """Taylor-linearization (mean, SE) for a continuous variable."""
    wsum = d[wcol].sum()
    m = (d[wcol] * d[ycol]).sum() / wsum
    d = d.copy()
    d["__z"] = d[wcol] * (d[ycol] - m) / wsum
    var = 0.0
    for _, g in d.groupby(strat):
        psu_sums = g.groupby(psu)["__z"].sum()
        mh = len(psu_sums)
        if mh <= 1:
            continue
        var += mh / (mh - 1) * ((psu_sums - psu_sums.mean()) ** 2).sum()
    return float(m), float(np.sqrt(var))


def _logit_ci(p: float, se: float) -> tuple[float, float]:
    z = 1.96
    lp = np.log(p / (1 - p))
    sl = se / (p * (1 - p))
    return (float(np.exp(lp - z * sl) / (1 + np.exp(lp - z * sl))),
            float(np.exp(lp + z * sl) / (1 + np.exp(lp + z * sl))))


def load_nhanes():
    demo, _ = pyreadstat.read_xport(str(CACHE / "NHANES_2021_2023" / "DEMO_L.xpt"), encoding="latin1")
    bmx, _ = pyreadstat.read_xport(str(CACHE / "NHANES_2021_2023" / "BMX_L.xpt"), encoding="latin1")
    return demo, bmx


def task1_asian_women():
    """Obesity prevalence among non-Hispanic Asian women age 50-69."""
    demo, bmx = load_nhanes()
    df = demo.merge(bmx[["SEQN", "BMXBMI"]], on="SEQN", how="inner")
    sub = df[
        (df["RIAGENDR"] == 2)
        & (df["RIDRETH3"] == 6)     # non-Hispanic Asian
        & (df["RIDAGEYR"] >= 50)
        & (df["RIDAGEYR"] <= 69)
        & (df["WTMEC2YR"] > 0)
        & df["BMXBMI"].notna()
    ].copy()
    sub["obese"] = (sub["BMXBMI"] >= 30).astype(int)
    p, se = _design_se_prev(sub, "obese", "WTMEC2YR")
    print(f"Task 1: Non-Hispanic Asian women 50-69 obesity = {100*p:.2f}% (SE {100*se:.2f}); n={len(sub)}")


def task2_education_obesity():
    """Obesity prevalence by education (<= HS vs >= college), with 95% Wilson CIs."""
    demo, bmx = load_nhanes()
    df = demo.merge(bmx[["SEQN", "BMXBMI"]], on="SEQN", how="inner")
    sub = df[(df["RIDAGEYR"] >= 25) & (df["WTMEC2YR"] > 0) & df["BMXBMI"].notna()
             & df["DMDEDUC2"].between(1, 5)].copy()
    sub["obese"] = (sub["BMXBMI"] >= 30).astype(int)
    sub["no_college"] = sub["DMDEDUC2"] <= 3   # less than some college
    p_low, se_low = _design_se_prev(sub[sub["no_college"]], "obese", "WTMEC2YR")
    p_high, se_high = _design_se_prev(sub[~sub["no_college"]], "obese", "WTMEC2YR")
    print(f"Task 2: no_college (<= HS) obesity = {100*p_low:.2f}% (SE {100*se_low:.2f})")
    print(f"        college+ obesity = {100*p_high:.2f}% (SE {100*se_high:.2f})")
    print(f"        diff = {100*(p_low-p_high):+.2f}pp")


def task3_age_extreme_difference():
    """Difference in obesity prevalence: women age 60+ minus men age 20-29."""
    demo, bmx = load_nhanes()
    df = demo.merge(bmx[["SEQN", "BMXBMI"]], on="SEQN", how="inner")
    sub = df[(df["WTMEC2YR"] > 0) & df["BMXBMI"].notna()].copy()
    sub["obese"] = (sub["BMXBMI"] >= 30).astype(int)
    a = sub[(sub["RIAGENDR"] == 2) & (sub["RIDAGEYR"] >= 60)]
    b = sub[(sub["RIAGENDR"] == 1) & (sub["RIDAGEYR"] >= 20) & (sub["RIDAGEYR"] <= 29)]
    pa, sea = _design_se_prev(a, "obese", "WTMEC2YR")
    pb, seb = _design_se_prev(b, "obese", "WTMEC2YR")
    # SE of difference using a single linearization across all data.
    s = sub[((sub["RIAGENDR"] == 2) & (sub["RIDAGEYR"] >= 60)) |
            ((sub["RIAGENDR"] == 1) & (sub["RIDAGEYR"] >= 20) & (sub["RIDAGEYR"] <= 29))].copy()
    s["__z"] = 0.0
    mask_a = (s["RIAGENDR"] == 2) & (s["RIDAGEYR"] >= 60)
    mask_b = (s["RIAGENDR"] == 1) & (s["RIDAGEYR"] >= 20) & (s["RIDAGEYR"] <= 29)
    s.loc[mask_a, "__z"] = s.loc[mask_a, "WTMEC2YR"] * (s.loc[mask_a, "obese"] - pa) / a["WTMEC2YR"].sum()
    s.loc[mask_b, "__z"] = -s.loc[mask_b, "WTMEC2YR"] * (s.loc[mask_b, "obese"] - pb) / b["WTMEC2YR"].sum()
    var = 0.0
    for _, g in s.groupby("SDMVSTRA"):
        psu_sums = g.groupby("SDMVPSU")["__z"].sum()
        m = len(psu_sums)
        if m <= 1: continue
        var += m / (m - 1) * ((psu_sums - psu_sums.mean()) ** 2).sum()
    se_d = np.sqrt(var)
    d = pa - pb
    print(f"Task 3: women 60+ obesity = {100*pa:.2f}%, men 20-29 obesity = {100*pb:.2f}%")
    print(f"        diff (W60+ - M20-29) = {100*d:+.2f}pp, SE diff = {100*se_d:.2f}, "
          f"CI = ({100*(d - 1.96*se_d):+.2f}, {100*(d + 1.96*se_d):+.2f})")


def task4_asian_to_white_income():
    """Ratio of Asian to non-Hispanic White median household income, 2023."""
    import openpyxl
    wb = openpyxl.load_workbook(str(CACHE / "CPS_ASEC_2024" / "tableA1.xlsx"), data_only=True)
    ws = wb.active
    asian = white = None
    for row in ws.iter_rows(values_only=True):
        if row[0] is None:
            continue
        s = str(row[0]).lstrip(".").strip().lower()
        if s == "asian":
            asian = row[5]
        elif s == "white, not hispanic":
            white = row[5]
    print(f"Task 4 (CPS): Asian = ${asian:,}, White non-Hispanic = ${white:,}")
    print(f"         Asian / White ratio = {100*asian/white:.2f}%")


def task5_high_impact_pain():
    """Among adults with chronic pain, share whose pain limits work/life."""
    with zipfile.ZipFile(CACHE / "NHIS_2023" / "adult23csv.zip") as z:
        with z.open("adult23.csv") as f:
            df = pd.read_csv(f, low_memory=False)
    # Chronic pain definition: PAIFRQ3M_A in [3,4]
    cp = df[(df["AGEP_A"] >= 18) & (df["WTFA_A"] > 0)
            & df["PAIFRQ3M_A"].isin([3, 4])].copy()
    # PAIWKLM3M_A: how often pain limits work/life — codes 1=never, 2=some days, 3=most days, 4=every day
    # "high impact" usually defined as PAIWKLM3M_A in [3,4] (most/every day)
    cp_valid = cp[cp["PAIWKLM3M_A"].between(1, 4)].copy()
    cp_valid["high_impact"] = cp_valid["PAIWKLM3M_A"].isin([3, 4]).astype(int)
    wsum = cp_valid["WTFA_A"].sum()
    p = (cp_valid["WTFA_A"] * cp_valid["high_impact"]).sum() / wsum
    # SE via NHIS Taylor
    cp_valid["__z"] = cp_valid["WTFA_A"] * (cp_valid["high_impact"] - p) / wsum
    var = 0.0
    for _, g in cp_valid.groupby("PSTRAT"):
        psu_sums = g.groupby("PPSU")["__z"].sum()
        m = len(psu_sums)
        if m <= 1: continue
        var += m / (m - 1) * ((psu_sums - psu_sums.mean()) ** 2).sum()
    se = np.sqrt(var)
    # Test against 50%
    z_stat = (p - 0.5) / se
    p_val = 2 * (1 - ss.norm.cdf(abs(z_stat)))
    print(f"Task 5: High-impact-among-chronic-pain = {100*p:.2f}% (SE {100*se:.2f})")
    print(f"         z vs 50% = {z_stat:.2f}, p = {p_val:.4g}")


def task6_bp_mean_diff():
    """Difference in mean SBP between adults 60+ and adults 20-39.
    Uses BPX_L (systolic blood pressure)."""
    demo, _ = pyreadstat.read_xport(str(CACHE / "NHANES_2021_2023" / "DEMO_L.xpt"), encoding="latin1")
    bpx, _ = pyreadstat.read_xport(str(CACHE / "NHANES_2021_2023" / "BPX_L.xpt"), encoding="latin1")
    # Use mean of available oscillometric readings 1-3 (BPXOSY{1,2,3}).
    bpx["SBP"] = bpx[["BPXOSY1", "BPXOSY2", "BPXOSY3"]].mean(axis=1)
    df = demo.merge(bpx[["SEQN", "SBP"]], on="SEQN", how="inner")
    sub = df[(df["WTMEC2YR"] > 0) & df["SBP"].notna()].copy()
    a = sub[sub["RIDAGEYR"] >= 60]
    b = sub[(sub["RIDAGEYR"] >= 20) & (sub["RIDAGEYR"] <= 39)]
    ma, sea = _design_se_mean(a, "SBP", "WTMEC2YR")
    mb, seb = _design_se_mean(b, "SBP", "WTMEC2YR")
    # Pooled SE via linearization
    s = sub[(sub["RIDAGEYR"] >= 60) | ((sub["RIDAGEYR"] >= 20) & (sub["RIDAGEYR"] <= 39))].copy()
    mask_a = s["RIDAGEYR"] >= 60
    mask_b = (s["RIDAGEYR"] >= 20) & (s["RIDAGEYR"] <= 39)
    s["__z"] = 0.0
    s.loc[mask_a, "__z"] = s.loc[mask_a, "WTMEC2YR"] * (s.loc[mask_a, "SBP"] - ma) / a["WTMEC2YR"].sum()
    s.loc[mask_b, "__z"] = -s.loc[mask_b, "WTMEC2YR"] * (s.loc[mask_b, "SBP"] - mb) / b["WTMEC2YR"].sum()
    var = 0.0
    for _, g in s.groupby("SDMVSTRA"):
        psu_sums = g.groupby("SDMVPSU")["__z"].sum()
        m = len(psu_sums)
        if m <= 1: continue
        var += m / (m - 1) * ((psu_sums - psu_sums.mean()) ** 2).sum()
    se_d = np.sqrt(var)
    d = ma - mb
    p_val = 2 * (1 - ss.norm.cdf(abs(d / se_d)))
    print(f"Task 6: mean SBP 60+ = {ma:.2f}, 20-39 = {mb:.2f}, diff = {d:+.2f}, SE_d = {se_d:.2f}, p = {p_val:.4g}")


def task7_industry_cs():
    """Within 'industry' sector (per the chart: Private for-profit + Self-employed),
    what % of doctorates are in Computer & Information Sciences fields."""
    import openpyxl
    wb = openpyxl.load_workbook(str(CACHE / "NSF_SDR_2023" / "nsf25321-tab012-001.xlsx"))
    ws = wb.active
    # Rows: All fields, Science, Bio..., ..., Computer & info sciences ...
    rows = list(ws.iter_rows(values_only=True))
    all_fields = next(r for r in rows if r[0] == "All fields")
    cs = next(r for r in rows if r[0] and "Computer and information" in str(r[0]))
    # cols: 4yr-ed=3, other-ed=5, for-profit=7, nonprofit=9, federal=11, state=13, self-emp=15, other=17
    ind_all = (all_fields[7] or 0) + (all_fields[15] or 0)
    ind_cs  = (cs[7] or 0) + (cs[15] or 0)
    print(f"Task 7: industry total = {ind_all:,.0f}, CS in industry = {ind_cs:,.0f}, share = {100*ind_cs/ind_all:.2f}%")


def task8_state_local_split():
    """For tax revenue: report (a) STATE government share of total state+local tax revenue,
    (b) LOCAL government share. Requires reading columns 3 (state) and 4 (local) within US block."""
    import openpyxl
    wb = openpyxl.load_workbook(str(CACHE / "ASFIN_2021" / "21slsstab1.xlsx"), data_only=True)
    ws = wb.active
    # Column layout for US: col 2 = state+local total, col 4 = state, col 5 = local
    for row in ws.iter_rows(values_only=True):
        if row[1] and str(row[1]).strip() == "Taxes":
            tax_total = row[2]
            tax_state = row[4]
            tax_local = row[5]
            print(f"Task 8: taxes total {tax_total:,}, state {tax_state:,}, local {tax_local:,}")
            print(f"        state share = {100*tax_state/tax_total:.2f}%, local share = {100*tax_local/tax_total:.2f}%")
            break


def task9_high_sodium_low_kcal():
    """Share of adult women (20+) with sodium > 2300mg AND energy < 1500 kcal/day."""
    demo, _ = pyreadstat.read_xport(str(CACHE / "NHANES_2021_2023" / "DEMO_L.xpt"), encoding="latin1")
    dr1, _ = pyreadstat.read_xport(str(CACHE / "NHANES_2021_2023" / "DR1TOT_L.xpt"), encoding="latin1")
    df = demo.merge(dr1[["SEQN", "DR1TSODI", "DR1TKCAL", "WTDRD1", "DR1DRSTZ"]], on="SEQN", how="inner")
    sub = df[(df["RIAGENDR"] == 2) & (df["RIDAGEYR"] >= 20) & (df["WTDRD1"] > 0)
             & (df["DR1DRSTZ"] == 1) & df["DR1TSODI"].notna() & df["DR1TKCAL"].notna()].copy()
    sub["target"] = ((sub["DR1TSODI"] > 2300) & (sub["DR1TKCAL"] < 1500)).astype(int)
    p, se = _design_se_prev(sub, "target", "WTDRD1")
    print(f"Task 9: women with Na>2300 & kcal<1500 = {100*p:.2f}% (SE {100*se:.2f}); n={len(sub)}")


def task10_race_sex_age_severe():
    """Severe obesity prevalence in 12 cells: race (NHW, NHB) x sex x age (20-39, 40-59, 60+)."""
    demo, bmx = load_nhanes()
    df = demo.merge(bmx[["SEQN", "BMXBMI"]], on="SEQN", how="inner")
    sub = df[(df["RIDAGEYR"] >= 20) & (df["WTMEC2YR"] > 0) & df["BMXBMI"].notna()].copy()
    sub["severe"] = (sub["BMXBMI"] >= 40).astype(int)
    out = {}
    for race_code, race_lbl in [(3, "nhw"), (4, "nhb")]:
        for sex_code, sex_lbl in [(1, "m"), (2, "f")]:
            for (lo, hi, age_lbl) in [(20, 39, "20_39"), (40, 59, "40_59"), (60, 200, "60p")]:
                d = sub[(sub["RIDRETH3"] == race_code)
                        & (sub["RIAGENDR"] == sex_code)
                        & (sub["RIDAGEYR"] >= lo) & (sub["RIDAGEYR"] <= hi)]
                p, se = _design_se_prev(d, "severe", "WTMEC2YR")
                key = f"{race_lbl}_{sex_lbl}_{age_lbl}"
                out[key] = (round(100 * p, 1), round(100 * se, 2), len(d))
    print("Task 10: 12-cell severe obesity prevalence (race x sex x age):")
    for k, (p, se, n) in out.items():
        print(f"  {k:18s}  {p:5.1f}%  (SE {se:4.2f},  n={n})")


if __name__ == "__main__":
    task1_asian_women()
    print()
    task2_education_obesity()
    print()
    task3_age_extreme_difference()
    print()
    task4_asian_to_white_income()
    print()
    task5_high_impact_pain()
    print()
    task6_bp_mean_diff()
    print()
    task7_industry_cs()
    print()
    task8_state_local_split()
    print()
    task9_high_sodium_low_kcal()
    print()
    task10_race_sex_age_severe()
