#!/bin/bash
# Oracle: design-adjusted linear regression of SBP on (age, male, BMI).
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


demo = read_messy("/data/demo_messy.csv")
suppl = read_messy("/data/demo_supplement.csv")    # not needed for this task
bmx = read_messy("/data/bmx_messy.csv")
bpx = read_messy("/data/bpx_messy.csv")

# Average SBP across readings 1-3, ignoring NaN.
bpx["SBP"] = bpx[["bp_osy_r1", "bp_osy_r2", "bp_osy_r3"]].mean(axis=1)

# Deduplicate on respondent_id (keep first plausible row).
for d in (demo, bmx, bpx):
    d.drop_duplicates(subset=["respondent_id"], keep="first", inplace=True)

df = (demo.merge(bmx[["respondent_id", "q_bmi_kgm2"]], on="respondent_id")
          .merge(bpx[["respondent_id", "SBP"]],        on="respondent_id"))

# Clean: drop implausible values + non-positive exam weight.
df = df[
    df["p_age_yr"].between(20, 100)
    & df["q_bmi_kgm2"].between(8, 100)
    & df["SBP"].between(40, 250)
    & (df["wt_mec_2yr"] > 0)
    & df["p_sex_code"].isin([1, 2])
].copy()

X = pd.DataFrame({
    "const": 1.0,
    "age":   df["p_age_yr"].astype(float),
    "male":  (df["p_sex_code"] == 1).astype(float),
    "bmi":   df["q_bmi_kgm2"].astype(float),
})
y = df["SBP"].astype(float).reset_index(drop=True)
w = df["wt_mec_2yr"].astype(float).reset_index(drop=True)
X = X.reset_index(drop=True)
strata = df["design_stratum"].astype(int).reset_index(drop=True)
psu = df["design_psu"].astype(int).reset_index(drop=True)

wls = sm.WLS(y, X, weights=w).fit()
beta_age = float(wls.params["age"])

# Design-adjusted Taylor sandwich SE.
e = y - wls.predict(X)
cols_x = list(X.columns)
s = X.mul((w * e).to_numpy(), axis=0)
s["__stratum"] = strata.to_numpy()
s["__psu"]     = psu.to_numpy()
psu_sums = s.groupby(["__stratum", "__psu"])[cols_x].sum().reset_index()
G = np.zeros((len(cols_x), len(cols_x)))
for _, g in psu_sums.groupby("__stratum"):
    m = len(g)
    if m <= 1:
        continue
    Z = g[cols_x].to_numpy() - g[cols_x].to_numpy().mean(axis=0, keepdims=True)
    G += m / (m - 1) * (Z.T @ Z)
XtWX = X.mul(w, axis=0).T @ X
XtWX_inv = np.linalg.inv(XtWX.to_numpy())
V = XtWX_inv @ G @ XtWX_inv
se_age = float(np.sqrt(V[cols_x.index("age"), cols_x.index("age")]))

out = {
    "beta_age": round(beta_age, 4),
    "se_age":   round(se_age, 4),
    "ci_lower": round(beta_age - 1.96 * se_age, 4),
    "ci_upper": round(beta_age + 1.96 * se_age, 4),
}
with open("/output/result.json", "w") as f:
    json.dump(out, f)
print(out)
PY
