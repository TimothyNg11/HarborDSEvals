#!/bin/bash
# Oracle: design-adjusted OR + Miettinen-Bruzzi PAF for high-impact pain
# by age (65+ vs 18-44) among adults with chronic pain.
set -e

python3 - <<'PY'
import json
import numpy as np
import pandas as pd
import statsmodels.api as sm

SENTINELS = ["", "NA", "REFUSED", "DK", "999.99", ".", "N/A"]


def read_messy(path):
    df = pd.read_csv(path, low_memory=False, dtype=str)
    df = df.replace(SENTINELS, np.nan)
    for c in df.columns:
        v = pd.to_numeric(df[c], errors="coerce")
        if v.notna().sum() > 0.5 * df[c].notna().sum():
            df[c] = v
    return df


df = read_messy("/data/nhis_adult_messy.csv")
df.drop_duplicates(subset=["respondent_id"], keep="first", inplace=True)

df = df[
    df["respondent_age"].between(18, 100)
    & (df["wt_sample_adult"] > 0)
    & df["pain_freq_3mo"].isin([3, 4])
    & df["pain_work_limit_3mo"].between(1, 4)
].copy()
df = df[(df["respondent_age"] <= 44) | (df["respondent_age"] >= 65)].copy()
df["age65plus"]   = (df["respondent_age"] >= 65).astype(int)
df["high_impact"] = df["pain_work_limit_3mo"].isin([3, 4]).astype(int)

y = df["high_impact"].astype(float).reset_index(drop=True)
X = pd.DataFrame({"const": 1.0, "age65plus": df["age65plus"].astype(float).values}).reset_index(drop=True)
w = df["wt_sample_adult"].astype(float).reset_index(drop=True)
strata = df["design_stratum"].astype(int).reset_index(drop=True)
psu = df["design_psu"].astype(int).reset_index(drop=True)

glm = sm.GLM(y, X, family=sm.families.Binomial(),
             freq_weights=w).fit(maxiter=200)
beta = float(glm.params["age65plus"])
OR = float(np.exp(beta))

# P(exposed | case)  using weighted proportion among y==1
cases = df[df["high_impact"] == 1]
p_exp_case = (cases["wt_sample_adult"] * cases["age65plus"]).sum() / cases["wt_sample_adult"].sum()
paf = float(p_exp_case * (OR - 1) / OR)

out = {
    "odds_ratio": round(OR, 2),
    "paf":        round(paf, 2),
}
with open("/output/result.json", "w") as f:
    json.dump(out, f)
print(out, f"  (beta={beta:.4f}, p_exp_case={p_exp_case:.4f})")
PY
