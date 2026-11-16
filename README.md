# Enterprise Data Detective — AI-Assisted Transaction Analytics

[![CI](https://github.com/kamjula/enterprise-data-detective/actions/workflows/ci.yml/badge.svg)](https://github.com/kamjula/enterprise-data-detective/actions/workflows/ci.yml) [![License: MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE)

A compact Python application for **profiling transaction data, surfacing explainable anomaly signals, and querying data in plain English**.

The project is intentionally small and inspectable: Pandas handles profiling and rules, DuckDB executes analytical SQL locally, and Claude converts natural-language questions into SELECT queries.

## What is implemented

| Capability | Implementation |
|---|---|
| Data profiling | Row/column counts, types, missing values, duplicates, numeric stats, date range |
| Anomaly review | Amount outliers, round-number amounts, velocity bursts, duplicate charges, high-risk-country and off-hours checks |
| Explainability | Every flagged row includes one or more human-readable reasons |
| Natural-language Q&A | Claude generates DuckDB SQL from a fixed transaction schema |
| Local analytics | DuckDB runs queries directly against the CSV |
| UI | Streamlit tabs for Profile, Anomalies, and AI Q&A |

## Application flow

```text
CSV / sample data
      │
      ├──> Pandas profiler ─────> data-quality summary
      │
      ├──> rule/stat checks ────> flagged transactions + reasons
      │
      └──> Claude SQL generation ──> DuckDB SELECT ──> result table
```

## AI safety boundary

The Q&A layer prompts Claude to use a fixed schema and rejects responses that do not begin with `SELECT`.

That is a **basic portfolio guard**, not a production SQL sandbox. A production version should use a proper SQL parser/AST validator, statement-count validation, query limits, timeouts, and isolated execution.

## Repository layout

```text
enterprise-data-detective/
├── app.py                      # Streamlit app: Profile, Anomalies, Ask (AI) tabs
├── requirements.txt
├── data/
│   ├── generate_sample_data.py # reproducible synthetic transactions (seed 42)
│   └── transactions.csv
├── detective/
│   ├── profile_data.py
│   ├── detect_anomalies.py
│   └── ask_claude.py
└── tests/
    └── test_detective.py
```

## Run locally

```bash
git clone https://github.com/kamjula/enterprise-data-detective.git
cd enterprise-data-detective

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python data/generate_sample_data.py
streamlit run app.py
```

To enable natural-language Q&A:

```bash
export ANTHROPIC_API_KEY=your-key-here
```

The modules also run on their own:

```bash
python detective/profile_data.py data/transactions.csv
python detective/detect_anomalies.py data/transactions.csv
python detective/ask_claude.py "top 5 merchants by total spend"
```

## Tests

```bash
pip install pytest
python -m pytest -q
```

The suite (run in CI on every push) checks the profiler's counts, that ordinary transactions are not flagged, that each anomaly rule fires with the right reason, and that the Q&A layer runs a generated SELECT against the data and refuses anything that is not a SELECT. Claude is replaced by a stub in the tests, so no API key is needed.

## Technical notes

- The included data is synthetic.
- Anomaly checks are heuristic review signals, not fraud labels or a validated fraud model.
- High-risk-country rules are hard-coded examples for the portfolio dataset and should not be treated as a real compliance policy.
- The application is local-first; no production deployment or customer-data claim is made.

## Stack

Python · Pandas · DuckDB · Streamlit · Claude API · pytest

## Author

**Sravani Kamjula** · AI/ML Engineer  
[LinkedIn](https://www.linkedin.com/in/sravani-kamjula/) · [Portfolio](https://sravaniportfoli.netlify.app/)
