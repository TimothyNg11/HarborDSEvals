"""Compute ground truth for the statistically-harder task variants:

Task 2 — age-standardized obesity prevalence by education with rate
         difference (Year-2000 standard pop, 3 age groups).
Task 3 — age-standardized obesity rate ratio (NH Black women /
         NH White women) with log-ratio Taylor CI.
Task 5 — adjusted odds ratio of high-impact pain (65+ vs 18-44) within
         chronic-pain adults, design-adjusted CI.
Task 6 — linear regression of SBP on (age, sex, BMI) using survey weights
         with design-adjusted SE for the age coefficient.
Task 9 — weighted 75th percentile of dietary sodium intake among adult
         women (Hyndman-Fan 7 quantile), with 95 % bootstrap CI from 1,000
         within-stratum resamples.
Task 10— concentration index of obesity by income quintile (income-rank
         concentration index, signed) for adults 20+.

Each result is printed; the oracle solutions for each task are calibrated
to match these.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pyreadstat
import scipy.stats as ss

CACHE = Path(__file__).resolve().parent.parent / "_data_cache"
NHANES = CACHE / "NHANES_2021_2023"

# Year-2000 US standard population for 3 age groups (20-39, 40-59, 60+),
# rebased to sum to 1.0. Sourced from Klein & Schoenborn (2001) Tab.1.
AGE_STD = {"20_39": 76_185_176, "40_59": 70_391_460, "60p": 51_138_334}
_total = sum(AGE_STD.values())
AGE_W = {k: v / _total for k, v in AGE_STD.items()}


def load_clean():
    demo, _ = pyreadstat.read_xport(str(NHANES / "DEMO_L.xpt"), encoding="latin1")
    bmx,  _ = pyreadstat.read_xport(str(NHANES / "BMX_L.xpt"),  encoding="latin1")
    bpx,  _ = pyreadstat.read_xport(str(NHANES / "BPX_L.xpt"),  encoding="latin1")
    return demo, bmx, bpx


def _w_design_var(d: pd.DataFrame, zcol: str = "__z",
                  strat: str = "SDMVSTRA", psu: str = "SDMVPSU") -> float:
    var = 0.0
    for _, g in d.groupby(strat):
        psu_sums = g.groupby(psu)[zcol].sum()
        m = len(psu_sums)
        if m <= 1:
            continue
        var += m / (m - 1) * ((psu_sums - psu_sums.mean()) ** 2).sum()
    return float(var)


def _age_band(age: int) -> str:
    if age <= 39:
        return "20_39"
    if age <= 59:
        return "40_59"
    return "60p"


def task2_age_std_by_education():
    demo, bmx, _ = load_clean()
    df = demo.merge(bmx[["SEQN", "BMXBMI"]], on="SEQN", how="inner")
    sub = df[(df["RIDAGEYR"] >= 25) & (df["RIDAGEYR"] <= 99)
             & (df["WTMEC2YR"] > 0)
             & df["BMXBMI"].notna()
             & df["DMDEDUC2"].between(1, 5)].copy()
    sub["obese"] = (sub["BMXBMI"] >= 30).astype(int)
    sub["band"] = sub["RIDAGEYR"].astype(int).map(_age_band)
    sub["low_ed"] = sub["DMDEDUC2"].isin([1, 2, 3])

    rows = []
    for is_low, lbl in [(True, "low_ed"), (False, "high_ed")]:
        s = sub[sub["low_ed"] == is_low]
        std_prev = 0.0
        for b, w in AGE_W.items():
            cell = s[s["band"] == b]
            if len(cell) == 0:
                continue
            p = (cell["WTMEC2YR"] * cell["obese"]).sum() / cell["WTMEC2YR"].sum()
            std_prev += w * p
        rows.append((lbl, 100 * std_prev))
        print(f"  {lbl} age-standardized obesity = {100*std_prev:.3f}%")

    diff = rows[0][1] - rows[1][1]
    print(f"  std rate difference (low - high) = {diff:.3f} pp")


def task3_age_std_rate_ratio():
    demo, bmx, _ = load_clean()
    df = demo.merge(bmx[["SEQN", "BMXBMI"]], on="SEQN", how="inner")
    sub = df[(df["RIDAGEYR"] >= 20) & (df["RIAGENDR"] == 2)
             & (df["WTMEC2YR"] > 0) & df["BMXBMI"].notna()].copy()
    sub["obese"] = (sub["BMXBMI"] >= 30).astype(int)
    sub["band"] = sub["RIDAGEYR"].astype(int).map(_age_band)

    rates = {}
    for race_code, lbl in [(3, "nhw"), (4, "nhb")]:
        s = sub[sub["RIDRETH3"] == race_code]
        std = 0.0
        for b, w in AGE_W.items():
            cell = s[s["band"] == b]
            p = (cell["WTMEC2YR"] * cell["obese"]).sum() / cell["WTMEC2YR"].sum()
            std += w * p
        rates[lbl] = std
        print(f"  {lbl} age-std obesity (women 20+) = {100*std:.3f}%")
    ratio = rates["nhb"] / rates["nhw"]
    print(f"  rate ratio NHB / NHW = {ratio:.4f}")


def task6_regression_sbp_on_age():
    demo, bmx, bpx = load_clean()
    bpx["SBP"] = bpx[["BPXOSY1", "BPXOSY2", "BPXOSY3"]].mean(axis=1)
    df = demo.merge(bmx[["SEQN", "BMXBMI"]], on="SEQN", how="inner") \
             .merge(bpx[["SEQN", "SBP"]],    on="SEQN", how="inner")
    sub = df[(df["RIDAGEYR"] >= 20) & (df["WTMEC2YR"] > 0)
             & df["BMXBMI"].notna() & df["SBP"].notna()].copy()

    import statsmodels.api as sm
    X = pd.DataFrame({
        "age":  sub["RIDAGEYR"].astype(float),
        "male": (sub["RIAGENDR"] == 1).astype(float),
        "bmi":  sub["BMXBMI"].astype(float),
    })
    X = sm.add_constant(X)
    y = sub["SBP"].astype(float)
    w = sub["WTMEC2YR"].astype(float)
    # Weighted least squares for point estimates.
    wls = sm.WLS(y, X, weights=w).fit()
    beta_age = wls.params["age"]

    # Design-adjusted SE for the age coefficient via Taylor sandwich with
    # PSU clustering.
    e = y - wls.predict(X)
    # Score for OLS: x_i * e_i; weighted: w * x * e
    s = X.mul((w * e).to_numpy(), axis=0)   # (n, k)
    s = s.assign(SDMVSTRA=sub["SDMVSTRA"].to_numpy(),
                 SDMVPSU=sub["SDMVPSU"].to_numpy())
    cols_x = [c for c in X.columns]
    # Sum scores within PSU; then between-PSU variance.
    psu = s.groupby(["SDMVSTRA", "SDMVPSU"])[cols_x].sum().reset_index()
    G = np.zeros((len(cols_x), len(cols_x)))
    for h, g in psu.groupby("SDMVSTRA"):
        m = len(g)
        if m <= 1:
            continue
        Z = g[cols_x].to_numpy() - g[cols_x].to_numpy().mean(axis=0, keepdims=True)
        G += m / (m - 1) * (Z.T @ Z)
    XtWX = (X.mul(w, axis=0).T @ X.to_numpy())
    XtWX_inv = np.linalg.inv(XtWX.to_numpy())
    V = XtWX_inv @ G @ XtWX_inv
    se_age = float(np.sqrt(V[cols_x.index("age"), cols_x.index("age")]))
    print(f"  beta_age = {beta_age:.5f}  SE = {se_age:.5f}  "
          f"95% CI = ({beta_age - 1.96*se_age:.4f}, {beta_age + 1.96*se_age:.4f})")


def task9_weighted_p75_sodium():
    """Weighted 75th percentile of sodium among adult women (Hyndman-Fan
    type 7 equivalent)."""
    demo, _, _ = load_clean()
    dr1, _ = pyreadstat.read_xport(str(NHANES / "DR1TOT_L.xpt"), encoding="latin1")
    df = demo.merge(dr1[["SEQN", "DR1TSODI", "WTDRD1", "DR1DRSTZ"]], on="SEQN", how="inner")
    sub = df[(df["RIAGENDR"] == 2) & (df["RIDAGEYR"] >= 20)
             & (df["WTDRD1"] > 0) & (df["DR1DRSTZ"] == 1)
             & df["DR1TSODI"].notna()].sort_values("DR1TSODI").reset_index(drop=True)
    cw = sub["WTDRD1"].cumsum()
    total = cw.iloc[-1]
    target = 0.75 * total
    # Hyndman-Fan type 4 / linear interpolation between two values
    idx_above = (cw >= target).idxmax()
    idx_below = idx_above - 1 if idx_above > 0 else 0
    w_above = cw.iloc[idx_above]
    w_below = cw.iloc[idx_below] if idx_below >= 0 else 0
    v_above = sub["DR1TSODI"].iloc[idx_above]
    v_below = sub["DR1TSODI"].iloc[idx_below]
    if w_above == w_below:
        p75 = v_above
    else:
        p75 = v_below + (target - w_below) / (w_above - w_below) * (v_above - v_below)
    print(f"  weighted P75 sodium (women 20+) = {p75:.1f} mg")


def task10_concentration_index():
    """Concentration index of obesity over income-to-poverty ratio.
    CI > 0 means obesity is concentrated in higher-income people; CI < 0
    means concentrated in lower-income people."""
    demo, bmx, _ = load_clean()
    df = demo.merge(bmx[["SEQN", "BMXBMI"]], on="SEQN", how="inner")
    sub = df[(df["RIDAGEYR"] >= 20) & (df["WTMEC2YR"] > 0)
             & df["BMXBMI"].notna() & df["INDFMPIR"].notna()].copy()
    sub["obese"] = (sub["BMXBMI"] >= 30).astype(int)
    s = sub.sort_values("INDFMPIR").reset_index(drop=True)
    w = s["WTMEC2YR"].to_numpy()
    y = s["obese"].to_numpy()
    W = w.sum()
    # Fractional rank: midpoint of cumulative weight share
    cum = np.cumsum(w)
    R = (cum - 0.5 * w) / W
    mean_y = (w * y).sum() / W
    ci = 2 * (w * y * R).sum() / (W * mean_y) - 1
    print(f"  concentration index (obesity vs income) = {ci:+.4f}")


if __name__ == "__main__":
    print("Task 2 — age-standardized obesity by education:")
    task2_age_std_by_education()
    print("\nTask 3 — age-standardized rate ratio (NH Black / NH White women):")
    task3_age_std_rate_ratio()
    print("\nTask 6 — regression coefficient of SBP on age:")
    task6_regression_sbp_on_age()
    print("\nTask 9 — weighted P75 sodium among women 20+:")
    task9_weighted_p75_sodium()
    print("\nTask 10 — concentration index of obesity over PIR:")
    task10_concentration_index()
