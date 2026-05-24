"""Re-compute the ground truth for each hardened task using ONLY the messy
CSVs. Confirms the right answer is still recoverable after cleaning."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import scipy.stats as ss

MESSY = Path(__file__).resolve().parent.parent / "_data_cache" / "_messy"

SENTINELS = {"", "NA", "REFUSED", "DK", "999.99", "9999"}


def _read(name: str) -> pd.DataFrame:
    df = pd.read_csv(MESSY / name, low_memory=False, dtype=str)
    # Coerce all sentinel cells to NaN
    df = df.replace(SENTINELS, np.nan)
    # Cast numerical-looking columns to float
    for c in df.columns:
        try:
            df[c] = pd.to_numeric(df[c])
        except (ValueError, TypeError):
            pass
    return df


def _clean_nhanes(df: pd.DataFrame) -> pd.DataFrame:
    if "p_age_yr" in df.columns:
        df = df[df["p_age_yr"].between(0, 100)]
    if "q_bmi_kgm2" in df.columns:
        df = df[df["q_bmi_kgm2"].between(8, 100)]
    if "wt_mec_2yr" in df.columns:
        df = df[df["wt_mec_2yr"] > 0]
    if "p_sex_code" in df.columns:
        df = df[df["p_sex_code"].isin([1, 2])]
    return df.copy()


def task1():
    demo = _read("demo_messy.csv")
    bmx  = _read("bmx_messy.csv")
    df = demo.merge(bmx[["respondent_id", "q_bmi_kgm2"]], on="respondent_id", how="inner")
    df = _clean_nhanes(df)
    sub = df[(df["p_sex_code"] == 2)
             & (df["p_race_eth_v3"] == 6)
             & (df["p_age_yr"] >= 50) & (df["p_age_yr"] <= 69)].copy()
    sub["obese"] = (sub["q_bmi_kgm2"] >= 30).astype(int)
    prev = 100 * (sub["wt_mec_2yr"] * sub["obese"]).sum() / sub["wt_mec_2yr"].sum()
    print(f"Task 1 (Asian women 50-69 obese): {prev:.2f}%  (n={len(sub)})  (truth: 13.08%)")


def task6():
    demo = _read("demo_messy.csv")
    bpx  = _read("bpx_messy.csv")
    bpx["SBP"] = bpx[["bp_osy_r1", "bp_osy_r2", "bp_osy_r3"]].mean(axis=1)
    df = demo.merge(bpx[["respondent_id", "SBP"]], on="respondent_id", how="inner")
    df = df[df["p_age_yr"].between(0, 100) & df["SBP"].between(40, 250) & (df["wt_mec_2yr"] > 0)]
    a = df[df["p_age_yr"] >= 60]
    b = df[(df["p_age_yr"] >= 20) & (df["p_age_yr"] <= 39)]
    ma = (a["wt_mec_2yr"] * a["SBP"]).sum() / a["wt_mec_2yr"].sum()
    mb = (b["wt_mec_2yr"] * b["SBP"]).sum() / b["wt_mec_2yr"].sum()
    print(f"Task 6: SBP 60+ = {ma:.2f}, 20-39 = {mb:.2f}, diff = {ma - mb:.2f}  (truth: ~15.9)")


def task5():
    df = _read("nhis_adult_messy.csv")
    df = df[df["respondent_age"].between(18, 100) & (df["wt_sample_adult"] > 0)]
    cp = df[df["pain_freq_3mo"].isin([3, 4]) & df["pain_work_limit_3mo"].between(1, 4)].copy()
    cp["high_impact"] = cp["pain_work_limit_3mo"].isin([3, 4]).astype(int)
    wsum = cp["wt_sample_adult"].sum()
    p = (cp["wt_sample_adult"] * cp["high_impact"]).sum() / wsum
    print(f"Task 5: high-impact among chronic pain = {100*p:.2f}%  (truth: 34.87%)")


def task9():
    demo = _read("demo_messy.csv")
    dr1  = _read("dr1tot_messy.csv")
    df = demo.merge(dr1[["respondent_id", "d1_total_kcal", "d1_total_sodium_mg",
                         "wt_drd1", "d1_recall_status"]], on="respondent_id", how="inner")
    df = df[(df["p_sex_code"] == 2) & (df["p_age_yr"].between(20, 100))
            & (df["wt_drd1"] > 0) & (df["d1_recall_status"] == 1)
            & df["d1_total_sodium_mg"].notna() & df["d1_total_kcal"].notna()].copy()
    df["target"] = ((df["d1_total_sodium_mg"] > 2300) & (df["d1_total_kcal"] < 1500)).astype(int)
    prev = 100 * (df["wt_drd1"] * df["target"]).sum() / df["wt_drd1"].sum()
    print(f"Task 9: Na>2300 & kcal<1500 (women 20+): {prev:.2f}%  (truth: 8.53%)")


if __name__ == "__main__":
    task1()
    task5()
    task6()
    task9()
