# Enterprise Data Detective — AI-Assisted Transaction Analytics

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

The runnable project currently lives one directory below the repository root:

```text
enterprise-data-detective/
└── enterprise-data-detective/
    ├── app.py
    ├── requirements.txt
    ├── data/
    └── detective/
        ├── profile_data.py
        ├── detect_anomalies.py
        └── ask_claude.py
```

## Run locally

```bash
git clone https://github.com/kamjula/enterprise-data-detective.git
cd enterprise-data-detective/enterprise-data-detective

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

## Technical notes

- The included data is synthetic.
- Anomaly checks are heuristic review signals, not fraud labels or a validated fraud model.
- High-risk-country rules are hard-coded examples for the portfolio dataset and should not be treated as a real compliance policy.
- The application is local-first; no production deployment or customer-data claim is made.

## Stack

Python · Pandas · DuckDB · Streamlit · Claude API

## Author

**Sravani Kamjula** · AI/ML Engineer  
[LinkedIn](https://www.linkedin.com/in/sravani-kamjula/) · [Portfolio](https://sravaniportfoli.netlify.app/)
