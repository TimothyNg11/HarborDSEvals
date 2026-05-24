"""Shared fee-rule matching engine for the original DABstep-style tasks.

Implements the DABstep manual's `fee = fixed_amount + rate * eur_amount / 10000`
formula and the rule-matching semantics implied by the dev-split answers:

    A fee rule applies to a transaction iff EVERY non-null rule field matches
    the transaction (lists treat empty == 'any value'; null == 'any value').

The engine computes per-transaction fees by summing across all matching
rules (some questions reuse this; others want only first-matching or only
specific rule subsets — see per-task notes).
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
CTX = ROOT / "_data_cache" / "DABstep" / "data" / "context"


def load_context():
    payments = pd.read_csv(CTX / "payments.csv")
    fees = json.load(open(CTX / "fees.json"))
    merchants = {m["merchant"]: m for m in json.load(open(CTX / "merchant_data.json"))}
    return payments, fees, merchants


def _list_ok(rule_field, txn_value):
    if rule_field is None:
        return True
    if isinstance(rule_field, list) and len(rule_field) == 0:
        return True
    if isinstance(rule_field, list):
        return txn_value in rule_field
    return rule_field == txn_value


def _capture_delay_ok(rule_cd, merchant_cd):
    """Manual's capture_delay rule values: '3-5', '>5', '<3', 'immediate',
    'manual'. The merchant's value is either one of those category strings,
    'immediate'/'manual', or a numeric-string day count (e.g. '1', '2', '4',
    '7'). Map both to the rule space and compare semantically.
    """
    if rule_cd is None:
        return True
    if merchant_cd is None:
        return False
    # If merchant value is already a rule-category string, direct match.
    if merchant_cd in ("immediate", "manual", "<3", "3-5", ">5"):
        return rule_cd == merchant_cd
    # Otherwise it's a numeric day count.
    try:
        d = int(merchant_cd)
    except (ValueError, TypeError):
        return False
    if rule_cd == "<3":   return d < 3
    if rule_cd == "3-5":  return 3 <= d <= 5
    if rule_cd == ">5":   return d > 5
    return False


def _intracountry_ok(rule_intra, ip_country, acquirer_country):
    if rule_intra is None:
        return True
    actual = ip_country == acquirer_country
    return bool(rule_intra) == actual


def rule_matches_txn(rule: dict, txn: pd.Series, merch: dict,
                     monthly_volume_bucket=None, monthly_fraud_level=None) -> bool:
    """Return True if the given rule applies to this transaction.

    `monthly_volume_bucket` and `monthly_fraud_level` are inputs because they
    depend on the rest of the month's transactions and so cannot be computed
    from a single row.
    """
    if rule["card_scheme"] != txn["card_scheme"]:
        return False
    if not _list_ok(rule.get("account_type"), merch.get("account_type")):
        return False
    if not _capture_delay_ok(rule.get("capture_delay"), merch.get("capture_delay")):
        return False
    if rule.get("monthly_fraud_level") is not None:
        if monthly_fraud_level != rule["monthly_fraud_level"]:
            return False
    if rule.get("monthly_volume") is not None:
        if monthly_volume_bucket != rule["monthly_volume"]:
            return False
    if not _list_ok(rule.get("merchant_category_code"),
                    merch.get("merchant_category_code")):
        return False
    if rule.get("is_credit") is not None:
        if bool(rule["is_credit"]) != bool(txn["is_credit"]):
            return False
    if not _list_ok(rule.get("aci"), txn["aci"]):
        return False
    if not _intracountry_ok(rule.get("intracountry"),
                            txn["ip_country"], txn["acquirer_country"]):
        return False
    return True


def compute_fee(rule: dict, eur_amount: float) -> float:
    return float(rule["fixed_amount"]) + float(rule["rate"]) * float(eur_amount) / 10000.0


def matching_rule_ids(rules, txn, merch, **kwargs):
    return [r["ID"] for r in rules if rule_matches_txn(r, txn, merch, **kwargs)]


def per_txn_total_fee(rules, txn, merch, **kwargs) -> float:
    """Sum fees across ALL matching rules for one transaction."""
    return sum(compute_fee(r, txn["eur_amount"])
               for r in rules if rule_matches_txn(r, txn, merch, **kwargs))


# ---- Monthly-bucket computation ---------------------------------------
# fees.json buckets:
#   monthly_volume:        '<100k', '100k-1m', '1m-5m', '>5m'  (EUR per month)
#   monthly_fraud_level:   '<7.2%', '7.2%-7.7%', '7.7%-8.3%', '>8.3%'

def _bucket_volume(total_eur: float) -> str:
    if total_eur < 100_000: return "<100k"
    if total_eur < 1_000_000: return "100k-1m"
    if total_eur < 5_000_000: return "1m-5m"
    return ">5m"


def _bucket_fraud(rate_pct: float) -> str:
    if rate_pct < 7.2:        return "<7.2%"
    if rate_pct <= 7.7:       return "7.2%-7.7%"
    if rate_pct <= 8.3:       return "7.7%-8.3%"
    return ">8.3%"


def compute_monthly_buckets(payments_df: pd.DataFrame,
                            merchant_name: str,
                            year: int = 2023) -> dict:
    """For each calendar month of `year`, compute the merchant's
    `monthly_volume_bucket` and `monthly_fraud_level` bucket strings
    that the DABstep fee rules key on.

    Volume = sum of `eur_amount` across the month.
    Fraud level = 100 * sum(eur_amount where has_fraudulent_dispute) /
                       sum(eur_amount).
    Returns: {1: (volume_bucket, fraud_bucket), 2: (...), ..., 12: (...)}.
    """
    sub = payments_df[(payments_df["merchant"] == merchant_name) &
                      (payments_df["year"] == year)].copy()
    if len(sub) == 0:
        return {m: (None, None) for m in range(1, 13)}
    sub["__d"] = pd.to_datetime(sub["day_of_year"].astype(int) - 1,
                                unit="D", origin=pd.Timestamp(f"{year}-01-01"))
    sub["month"] = sub["__d"].dt.month
    out = {}
    for m in range(1, 13):
        rows = sub[sub["month"] == m]
        vol = float(rows["eur_amount"].sum())
        fraud_vol = float(rows[rows["has_fraudulent_dispute"] == True]["eur_amount"].sum())
        fraud_pct = (100 * fraud_vol / vol) if vol > 0 else 0.0
        out[m] = (_bucket_volume(vol), _bucket_fraud(fraud_pct))
    return out


def per_txn_total_fee_with_buckets(rules, txn, merch,
                                    monthly_buckets: dict) -> float:
    """Like `per_txn_total_fee` but resolves the txn's monthly bucket
    from the precomputed table. `monthly_buckets` maps month-int -> (vol, fraud)."""
    # Derive month from day_of_year (2023 non-leap)
    day = int(txn["day_of_year"])
    import datetime
    d = datetime.date(int(txn["year"]), 1, 1) + datetime.timedelta(days=day - 1)
    m = d.month
    vol_bucket, fraud_bucket = monthly_buckets.get(m, (None, None))
    return sum(compute_fee(r, txn["eur_amount"])
               for r in rules if rule_matches_txn(
                   r, txn, merch,
                   monthly_volume_bucket=vol_bucket,
                   monthly_fraud_level=fraud_bucket,
               ))


def matching_rule_ids_with_buckets(rules, txn, merch, monthly_buckets: dict):
    import datetime
    day = int(txn["day_of_year"])
    d = datetime.date(int(txn["year"]), 1, 1) + datetime.timedelta(days=day - 1)
    m = d.month
    vol_bucket, fraud_bucket = monthly_buckets.get(m, (None, None))
    return [r["ID"] for r in rules if rule_matches_txn(
        r, txn, merch,
        monthly_volume_bucket=vol_bucket,
        monthly_fraud_level=fraud_bucket,
    )]
