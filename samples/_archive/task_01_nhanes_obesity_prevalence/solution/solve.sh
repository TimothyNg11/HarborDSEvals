#!/bin/bash
# Oracle: 4-condition compound subgroup obesity prevalence + Wilson CI
# on the design-effective sample size.
set -e

python3 - <<'PY'
import json
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


demo = read_messy("/data/demo_messy.csv")
suppl = read_messy("/data/demo_supplement.csv")
bmx = read_messy("/data/bmx_messy.csv")
for d in (demo, suppl, bmx):
    d.drop_duplicates(subset=["respondent_id"], keep="first", inplace=True)

df = (demo
      .merge(suppl[["respondent_id", "p_us_born"]], on="respondent_id", how="left")
      .merge(bmx[["respondent_id", "q_bmi_kgm2"]],   on="respondent_id"))

sub = df[
    (df["p_sex_code"] == 2)
    & (df["p_race_eth_v3"] == 6)
    & df["p_age_yr"].between(50, 69)
    & (df["p_us_born"] == 2)
    & df["q_bmi_kgm2"].between(8, 100)
    & (df["wt_mec_2yr"] > 0)
].copy()
sub["obese"] = (sub["q_bmi_kgm2"] >= 30).astype(int)

n_raw = len(sub)
wsum = sub["wt_mec_2yr"].sum()
p = (sub["wt_mec_2yr"] * sub["obese"]).sum() / wsum

# Design effect (DEFF) via Taylor variance vs binomial variance
sub["__z"] = sub["wt_mec_2yr"] * (sub["obese"] - p) / wsum
v_design = 0.0
for _, g in sub.groupby("design_stratum"):
    psu_sums = g.groupby("design_psu")["__z"].sum()
    m = len(psu_sums)
    if m <= 1:
        continue
    v_design += m / (m - 1) * ((psu_sums - psu_sums.mean()) ** 2).sum()
v_binom = p * (1 - p) / n_raw
deff = v_design / v_binom if v_binom > 0 else 1.0
n_eff = n_raw / deff if deff > 0 else n_raw

z = 1.96
denom = n_eff + z * z
center = (n_eff * p + z * z / 2) / denom
half = z * np.sqrt((n_eff * p * (1 - p) + z * z / 4) / (denom ** 2))
lo = max(0.0, center - half)
hi = min(1.0, center + half)

out = {
    "prevalence": round(100 * float(p),  2),
    "ci_lower":   round(100 * float(lo), 2),
    "ci_upper":   round(100 * float(hi), 2),
}
with open("/output/result.json", "w") as f:
    json.dump(out, f)
print(out, f"  (n_raw={n_raw}, deff={deff:.3f}, n_eff={n_eff:.2f})")
PY
