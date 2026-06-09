"""
Generate a synthetic enterprise transactions dataset.

This data is FAKE / randomly generated -- it is only meant to demo the
Data Detective tool. We deliberately inject a small number of suspicious
transactions so the anomaly detector has something realistic to find.

Run:  python data/generate_sample_data.py
Output:  data/transactions.csv
"""

import csv
import random
from datetime import datetime, timedelta

random.seed(42)  # makes the output reproducible

N_NORMAL = 5000          # number of normal transactions
N_ACCOUNTS = 200         # number of customer accounts
OUTPUT = "data/transactions.csv"

MERCHANTS = [
    "Amazon", "Walmart", "Starbucks", "Shell", "Uber", "Netflix",
    "Apple", "Target", "Costco", "Delta Airlines", "Marriott", "BestBuy",
]
CATEGORIES = {
    "Amazon": "Retail", "Walmart": "Retail", "Target": "Retail",
    "Costco": "Retail", "BestBuy": "Electronics", "Apple": "Electronics",
    "Starbucks": "Food", "Shell": "Fuel", "Uber": "Travel",
    "Delta Airlines": "Travel", "Marriott": "Travel", "Netflix": "Subscription",
}
COUNTRIES = ["US"] * 92 + ["CA", "GB", "DE", "MX"] * 2  # mostly US
CHANNELS = ["online", "in_store", "atm", "mobile"]

start = datetime(2025, 1, 1)
rows = []
txn_id = 1


def make_row(account, when, amount, merchant, country, channel):
    global txn_id
    row = {
        "transaction_id": f"T{txn_id:06d}",
        "timestamp": when.strftime("%Y-%m-%d %H:%M:%S"),
        "account_id": f"A{account:04d}",
        "merchant": merchant,
        "category": CATEGORIES.get(merchant, "Other"),
        "amount": round(amount, 2),
        "country": country,
        "channel": channel,
    }
    txn_id += 1
    return row


# ---- 1. Normal transactions -------------------------------------------------
for _ in range(N_NORMAL):
    account = random.randint(1, N_ACCOUNTS)
    when = start + timedelta(
        days=random.randint(0, 150),
        hours=random.randint(7, 21),      # normal daytime hours
        minutes=random.randint(0, 59),
    )
    merchant = random.choice(MERCHANTS)
    amount = round(random.uniform(5, 400), 2)   # typical spend
    rows.append(make_row(account, when, amount, merchant,
                         random.choice(COUNTRIES), random.choice(CHANNELS)))

# ---- 2. Injected anomalies (the stuff we WANT the detector to catch) --------
# 2a. A few very large round-number transactions
for _ in range(15):
    account = random.randint(1, N_ACCOUNTS)
    when = start + timedelta(days=random.randint(0, 150), hours=random.randint(0, 23))
    amount = random.choice([5000, 10000, 15000, 25000])
    rows.append(make_row(account, when, amount, "Apple", "US", "online"))

# 2b. Velocity bursts -- one account hammering many transactions in minutes
for burst in range(5):
    account = random.randint(1, N_ACCOUNTS)
    base = start + timedelta(days=random.randint(0, 150), hours=random.randint(0, 23))
    for k in range(12):
        when = base + timedelta(minutes=k)  # 12 txns in 12 minutes
        rows.append(make_row(account, when, round(random.uniform(200, 900), 2),
                             random.choice(MERCHANTS), "US", "online"))

# 2c. Exact duplicate charges (same account, merchant, amount, near in time)
for _ in range(10):
    account = random.randint(1, N_ACCOUNTS)
    when = start + timedelta(days=random.randint(0, 150), hours=random.randint(7, 21))
    amt = round(random.uniform(50, 300), 2)
    m = random.choice(MERCHANTS)
    rows.append(make_row(account, when, amt, m, "US", "online"))
    rows.append(make_row(account, when + timedelta(minutes=2), amt, m, "US", "online"))

# 2d. Off-hours foreign transactions
for _ in range(12):
    account = random.randint(1, N_ACCOUNTS)
    when = start + timedelta(days=random.randint(0, 150), hours=random.choice([1, 2, 3, 4]))
    rows.append(make_row(account, when, round(random.uniform(300, 1200), 2),
                         random.choice(MERCHANTS), random.choice(["RU", "NG", "CN"]), "online"))

# ---- 3. Shuffle and write ---------------------------------------------------
random.shuffle(rows)

with open(OUTPUT, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)

print(f"Wrote {len(rows)} transactions to {OUTPUT}")
