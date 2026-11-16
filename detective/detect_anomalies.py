"""
Anomaly / fraud detector.

Flags suspicious transactions using a mix of statistical and rule-based
checks. Each flagged row comes with a human-readable REASON so an analyst
knows *why* it was surfaced -- this is what makes the output useful for
manual review rather than a black box.

Checks:
  1. Large-amount outliers   (z-score on amount)
  2. Big round numbers       (e.g. exactly 5000, 10000)
  3. Velocity bursts         (many transactions per account in a short window)
  4. Duplicate charges       (same account + merchant + amount, minutes apart)
  5. Foreign / off-hours     (high-risk country or 12am-5am activity)

Run:  python detective/detect_anomalies.py data/transactions.csv
"""

import sys
import pandas as pd

HIGH_RISK_COUNTRIES = {"RU", "NG", "CN"}


def detect(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    # Each transaction can collect one or more reasons
    reasons = {i: [] for i in df.index}

    # 1. Large-amount outliers (global z-score > 3)
    mean, std = df["amount"].mean(), df["amount"].std()
    if std > 0:
        z = (df["amount"] - mean) / std
        for i in df.index[z > 3]:
            reasons[i].append(f"amount z-score {z[i]:.1f} (far above average)")

    # 2. Big round-number amounts
    for i in df.index[(df["amount"] >= 1000) & (df["amount"] % 1000 == 0)]:
        reasons[i].append("large round-number amount")

    # 3. Velocity bursts: >=6 transactions by one account within 15 minutes
    df_sorted = df.sort_values(["account_id", "timestamp"])
    for acct, grp in df_sorted.groupby("account_id"):
        times = grp["timestamp"].values
        idx = grp.index.values
        for j in range(len(times)):
            window = (times >= times[j]) & (times < times[j] + pd.Timedelta(minutes=15))
            if window.sum() >= 6:
                for i in idx[window]:
                    if "velocity burst" not in reasons[i]:
                        reasons[i].append("velocity burst")

    # 4. Duplicate charges: same account+merchant+amount within 5 minutes
    key = ["account_id", "merchant", "amount"]
    for _, grp in df_sorted.groupby(key):
        if len(grp) < 2:
            continue
        t = grp["timestamp"].sort_values()
        gaps = t.diff().dt.total_seconds().fillna(9e9)
        for i in grp.index[gaps.values < 300]:
            reasons[i].append("possible duplicate charge")

    # 5. Foreign high-risk country OR off-hours (00:00-05:00)
    for i in df.index[df["country"].isin(HIGH_RISK_COUNTRIES)]:
        reasons[i].append(f"high-risk country ({df.at[i, 'country']})")
    hours = df["timestamp"].dt.hour
    for i in df.index[(hours >= 0) & (hours < 5)]:
        reasons[i].append("off-hours activity")

    df["flag_reasons"] = [", ".join(reasons[i]) for i in df.index]
    flagged = df[df["flag_reasons"] != ""].sort_values("amount", ascending=False)
    return flagged


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "data/transactions.csv"
    df = pd.read_csv(path)
    flagged = detect(df)
    total = len(df)
    print(f"\n=== ANOMALY REPORT ===")
    print(f"{len(flagged)} of {total} transactions flagged "
          f"({len(flagged)/total*100:.1f}%)\n")
    cols = ["transaction_id", "account_id", "merchant", "amount",
            "country", "flag_reasons"]
    with pd.option_context("display.max_colwidth", 40, "display.width", 120):
        print(flagged[cols].head(20).to_string(index=False))
