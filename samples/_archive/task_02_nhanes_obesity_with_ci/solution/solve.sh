#!/bin/bash
# Oracle: age-standardized obesity prevalence by education (low vs high).
set -e

python3 - <<'PY'
import json
import numpy as np
import pandas as pd

SENTINELS = ["", "NA", "REFUSED", "DK", "999.99", ".", "N/A"]
STD_W = {"20_39": 76_185_176, "40_59": 70_391_460, "60p": 51_138_334}
total = sum(STD_W.values())
AGE_W = {k: v / total for k, v in STD_W.items()}


def read_messy(path):
    df = pd.read_csv(path, low_memory=False, dtype=str)
    df = df.replace(SENTINELS, np.nan)
    for c in df.columns:
        v = pd.to_numeric(df[c], errors="coerce")
        if v.notna().sum() > 0.5 * df[c].notna().sum():
            df[c] = v
    return df


demo = read_messy("/data/demo_messy.csv")
suppl = read_messy("/data/demo_supplement.csv")
bmx = read_messy("/data/bmx_messy.csv")

for d in (demo, suppl, bmx):
    d.drop_duplicates(subset=["respondent_id"], keep="first", inplace=True)

df = (demo
      .merge(suppl[["respondent_id", "p_education_max"]], on="respondent_id", how="inner")
      .merge(bmx[["respondent_id", "q_bmi_kgm2"]],         on="respondent_id"))

df = df[
    df["p_age_yr"].between(25, 100)
    & df["q_bmi_kgm2"].between(8, 100)
    & (df["wt_mec_2yr"] > 0)
    & df["p_education_max"].between(1, 5)
].copy()
df["obese"] = (df["q_bmi_kgm2"] >= 30).astype(int)


def age_band(age):
    if age <= 39:
        return "20_39"
    if age <= 59:
        return "40_59"
    return "60p"


df["band"] = df["p_age_yr"].astype(int).map(age_band)
df["low_ed"] = df["p_education_max"].isin([1, 2, 3])


def std_prev(d):
    out = 0.0
    for band, w in AGE_W.items():
        cell = d[d["band"] == band]
        if len(cell) == 0:
            continue
        p = (cell["wt_mec_2yr"] * cell["obese"]).sum() / cell["wt_mec_2yr"].sum()
        out += w * p
    return out


low  = 100 * std_prev(df[df["low_ed"]])
high = 100 * std_prev(df[~df["low_ed"]])
out = {
    "low_ed_std_prev":  round(low, 2),
    "high_ed_std_prev": round(high, 2),
    "rate_difference":  round(low - high, 2),
}
with open("/output/result.json", "w") as f:
    json.dump(out, f)
print(out)
PY
