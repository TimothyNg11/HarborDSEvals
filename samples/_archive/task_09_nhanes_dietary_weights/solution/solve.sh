#!/bin/bash
# Oracle: weighted MAD around the weighted median of sodium intake among
# adult women.
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


def weighted_quantile(values, weights, q):
    order = np.argsort(values)
    v = np.asarray(values)[order]
    w = np.asarray(weights)[order]
    cw = np.cumsum(w)
    total = cw[-1]
    target = q * total
    i_above = int(np.searchsorted(cw, target, side="left"))
    i_below = max(i_above - 1, 0)
    w_above, w_below = cw[i_above], cw[i_below]
    v_above, v_below = v[i_above], v[i_below]
    if w_above == w_below:
        return float(v_above)
    return float(v_below + (target - w_below) / (w_above - w_below) * (v_above - v_below))


demo = read_messy("/data/demo_messy.csv")
dr1  = read_messy("/data/dr1tot_messy.csv")
for d in (demo, dr1):
    d.drop_duplicates(subset=["respondent_id"], keep="first", inplace=True)

df = demo.merge(
    dr1[["respondent_id", "d1_total_sodium_mg", "wt_drd1", "d1_recall_status"]],
    on="respondent_id",
)
df = df[
    (df["p_sex_code"] == 2)
    & df["p_age_yr"].between(20, 100)
    & (df["wt_drd1"] > 0)
    & (df["d1_recall_status"] == 1)
    & df["d1_total_sodium_mg"].notna()
].copy()

x = df["d1_total_sodium_mg"].to_numpy(dtype=float)
w = df["wt_drd1"].to_numpy(dtype=float)

m = weighted_quantile(x, w, 0.5)
d = np.abs(x - m)
wmad = weighted_quantile(d, w, 0.5)

with open("/output/result.txt", "w") as f:
    f.write(f"{round(float(wmad), 1)}")
print(f"weighted median = {m:.1f} mg; wMAD = {round(float(wmad), 1)} mg")
PY
