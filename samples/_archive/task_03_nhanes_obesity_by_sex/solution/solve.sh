#!/bin/bash
# Oracle: age-standardized rate ratio of obesity (NHB / NHW women).
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
bmx = read_messy("/data/bmx_messy.csv")
for d in (demo, bmx):
    d.drop_duplicates(subset=["respondent_id"], keep="first", inplace=True)

df = demo.merge(bmx[["respondent_id", "q_bmi_kgm2"]], on="respondent_id")
df = df[(df["p_sex_code"] == 2) & df["p_age_yr"].between(20, 100)
        & df["q_bmi_kgm2"].between(8, 100) & (df["wt_mec_2yr"] > 0)].copy()
df["obese"] = (df["q_bmi_kgm2"] >= 30).astype(int)


def band(age):
    if age <= 39: return "20_39"
    if age <= 59: return "40_59"
    return "60p"


df["band"] = df["p_age_yr"].astype(int).map(band)


def std_prev(d):
    out = 0.0
    for b, w in AGE_W.items():
        cell = d[d["band"] == b]
        if len(cell) == 0: continue
        p = (cell["wt_mec_2yr"] * cell["obese"]).sum() / cell["wt_mec_2yr"].sum()
        out += w * p
    return out


nhb = 100 * std_prev(df[df["p_race_eth_v3"] == 4])
nhw = 100 * std_prev(df[df["p_race_eth_v3"] == 3])
out = {
    "nhb_std_prev": round(nhb, 2),
    "nhw_std_prev": round(nhw, 2),
    "rate_ratio":   round(nhb / nhw, 4),
}
with open("/output/result.json", "w") as f:
    json.dump(out, f)
print(out)
PY
