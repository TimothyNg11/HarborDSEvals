#!/bin/bash
# Oracle: Erreygers concentration index of severe obesity (BMI >= 40)
# over family income-to-poverty ratio.
set -e

python3 - <<'PY'
import numpy as np
import pandas as pd

SENTINELS = ["", "NA", "REFUSED", "DK", "999.99", ".", "N/A"]


def read_messy(path):
    df = pd.read_csv(path, low_memory=False, dtype=str)
    df = df.replace(SENTINELS, np.nan)
    for c in df.columns:
        v = pd.to_numeric(df[c], errors="coerce")
        if v.notna().sum() > 0.5 * df[c].notna().sum():
            df[c] = v
    return df


demo  = read_messy("/data/demo_messy.csv")
suppl = read_messy("/data/demo_supplement.csv")
bmx   = read_messy("/data/bmx_messy.csv")
for d in (demo, suppl, bmx):
    d.drop_duplicates(subset=["respondent_id"], keep="first", inplace=True)

df = (demo
      .merge(suppl[["respondent_id", "p_pir_ratio"]], on="respondent_id", how="left")
      .merge(bmx[["respondent_id", "q_bmi_kgm2"]],     on="respondent_id"))

df = df[
    df["p_age_yr"].between(20, 100)
    & df["q_bmi_kgm2"].between(8, 100)
    & (df["wt_mec_2yr"] > 0)
    & df["p_pir_ratio"].between(0, 5.001)
].copy()
df["severe"] = (df["q_bmi_kgm2"] >= 40).astype(int)
df = df.sort_values("p_pir_ratio").reset_index(drop=True)

w = df["wt_mec_2yr"].to_numpy()
y = df["severe"].to_numpy()
W = w.sum()
cum = np.cumsum(w)
R = (cum - 0.5 * w) / W
mu_y = (w * y).sum() / W
C = 2 * (w * y * R).sum() / (W * mu_y) - 1
E = 4 * mu_y * (1 - mu_y) * C

with open("/output/result.txt", "w") as f:
    f.write(f"{round(float(E), 4)}")
print(f"Erreygers E = {round(float(E), 4)}  (standard C = {C:.4f}, mu_y = {mu_y:.4f})")
PY
