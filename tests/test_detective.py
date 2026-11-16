# checks for the profiler, the anomaly rules and the SQL guard in the Q&A layer.
# run from the repo root: python -m pytest -q

from types import SimpleNamespace

import pandas as pd
import pytest

import detective.ask_claude as ask_claude
from detective.detect_anomalies import detect
from detective.profile_data import profile

COLUMNS = ["transaction_id", "timestamp", "account_id", "merchant",
           "category", "amount", "country", "channel"]


def row(tid, ts, account, merchant, amount, country="US"):
    return [tid, ts, account, merchant, "Retail", amount, country, "online"]


def ordinary(n=40):
    # daytime purchases, different accounts and days, no repeated amounts
    return [row(f"T{i:03d}", f"2025-03-{1 + i % 28:02d} {9 + i % 8:02d}:15:00",
                f"A{i % 10:03d}", "Shop", 20.0 + i) for i in range(n)]


def frame(rows):
    return pd.DataFrame(rows, columns=COLUMNS)


def reasons_for(flagged, tid):
    hit = flagged.loc[flagged["transaction_id"] == tid, "flag_reasons"]
    return hit.iloc[0] if len(hit) else ""


# profiler

def test_profile_reports_shape_missing_duplicates_and_dates():
    rows = ordinary(5)
    rows.append(rows[0])                                  # one exact duplicate
    rows.append(row("T900", "2025-03-30 10:00:00", None, "Shop", 12.5))
    rep = profile(frame(rows))
    assert rep["rows"] == 7
    assert rep["columns"] == len(COLUMNS)
    assert rep["duplicate_rows"] == 1
    account = next(c for c in rep["columns_detail"] if c["column"] == "account_id")
    assert account["missing"] == 1
    assert rep["date_range"]["column"] == "timestamp"
    assert rep["date_range"]["max"].startswith("2025-03-30")


# anomaly rules

def test_ordinary_transactions_are_not_flagged():
    assert detect(frame(ordinary())).empty


def test_large_round_amount_is_flagged():
    flagged = detect(frame(ordinary() + [row("X1", "2025-03-10 11:00:00", "A001", "Shop", 5000.0)]))
    assert "large round-number amount" in reasons_for(flagged, "X1")


def test_amount_far_above_average_is_flagged():
    flagged = detect(frame(ordinary() + [row("X1", "2025-03-10 11:00:00", "A001", "Shop", 987.65)]))
    assert "amount z-score" in reasons_for(flagged, "X1")


def test_velocity_burst_flags_every_transaction_in_the_burst():
    burst = [row(f"B{i}", f"2025-03-12 14:{i * 2:02d}:00", "A777", f"Store{i}", 30.0 + i)
             for i in range(6)]
    flagged = detect(frame(ordinary() + burst))
    for i in range(6):
        assert "velocity burst" in reasons_for(flagged, f"B{i}")


def test_repeat_charge_minutes_apart_is_flagged():
    dupes = [row("D1", "2025-03-15 12:00:00", "A555", "Cafe", 42.0),
             row("D2", "2025-03-15 12:02:00", "A555", "Cafe", 42.0)]
    flagged = detect(frame(ordinary() + dupes))
    assert "possible duplicate charge" in reasons_for(flagged, "D2")


def test_high_risk_country_and_off_hours_are_flagged():
    extra = [row("C1", "2025-03-16 13:00:00", "A321", "Shop", 55.0, country="RU"),
             row("H1", "2025-03-16 02:30:00", "A322", "Shop", 56.0)]
    flagged = detect(frame(ordinary() + extra))
    assert "high-risk country (RU)" in reasons_for(flagged, "C1")
    assert "off-hours activity" in reasons_for(flagged, "H1")


# natural-language Q&A (Claude is replaced by a stub, so no API key is needed)

def stub_claude(monkeypatch, reply):
    message = SimpleNamespace(content=[SimpleNamespace(text=reply)])
    client = SimpleNamespace(messages=SimpleNamespace(create=lambda **kwargs: message))
    monkeypatch.setattr(ask_claude, "Anthropic", lambda: client)


@pytest.fixture
def csv_path(tmp_path, monkeypatch):
    path = tmp_path / "transactions.csv"
    frame(ordinary()).to_csv(path, index=False)
    monkeypatch.setattr(ask_claude, "CSV_PATH", str(path))
    return path


def test_generated_select_runs_against_the_data(monkeypatch, csv_path):
    stub_claude(monkeypatch, "```sql\nSELECT COUNT(*) AS n FROM txns\n```")
    out = ask_claude.ask("how many transactions are there?")
    assert out["sql"] == "SELECT COUNT(*) AS n FROM txns"
    assert int(out["result"]["n"].iloc[0]) == 40


def test_non_select_sql_is_refused(monkeypatch, csv_path):
    stub_claude(monkeypatch, "DROP TABLE txns")
    with pytest.raises(ValueError, match="non-SELECT"):
        ask_claude.ask("delete everything")
