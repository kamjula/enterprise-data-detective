"""
Natural-language Q&A over the transactions data, powered by Claude.

The user asks a question in plain English (e.g. "which 5 accounts spent the
most in March?"). We send Claude the table schema and ask it to write a
single safe SELECT query. We run that query with DuckDB and return the result.

This is the "AI" in AI-Powered Data Detective: instead of writing SQL by
hand, an analyst can interrogate the data in plain language.

Requires an API key in the environment:  export ANTHROPIC_API_KEY=sk-ant-...
Run:  python detective/ask_claude.py "top 5 merchants by total amount"
"""

import os
import sys
import re
import duckdb
import pandas as pd
from anthropic import Anthropic

CSV_PATH = "data/transactions.csv"
MODEL = "claude-sonnet-4-6"   # fast + cheap; good for SQL generation

SCHEMA = """
Table name: txns
Columns:
  transaction_id  TEXT     -- unique id, e.g. 'T000123'
  timestamp       TIMESTAMP-- when the transaction happened
  account_id      TEXT     -- customer account, e.g. 'A0042'
  merchant        TEXT     -- e.g. 'Amazon', 'Uber'
  category        TEXT     -- e.g. 'Retail', 'Travel'
  amount          DOUBLE   -- transaction amount in USD
  country         TEXT     -- 2-letter code, e.g. 'US'
  channel         TEXT     -- 'online', 'in_store', 'atm', 'mobile'
"""

PROMPT = """You are a SQL assistant for a DuckDB database.
{schema}

Write a single DuckDB SQL query that answers the user's question.
Rules:
- Use only the table and columns above.
- Output ONLY the SQL query, no explanation, no markdown fences.
- It MUST be a SELECT query (never INSERT/UPDATE/DELETE/DROP).

User question: {question}"""


def ask(question: str) -> dict:
    """Turn a natural-language question into SQL, run it, return the result."""
    client = Anthropic()  # reads ANTHROPIC_API_KEY from the environment

    # 1. Ask Claude to write the SQL
    msg = client.messages.create(
        model=MODEL,
        max_tokens=500,
        messages=[{
            "role": "user",
            "content": PROMPT.format(schema=SCHEMA, question=question),
        }],
    )
    sql = msg.content[0].text.strip()
    sql = re.sub(r"^```(?:sql)?|```$", "", sql, flags=re.MULTILINE).strip()

    # 2. Safety check: only allow read-only SELECT queries
    if not sql.lower().lstrip().startswith("select"):
        raise ValueError(f"Refusing to run non-SELECT query:\n{sql}")

    # 3. Run the query with DuckDB against the CSV
    con = duckdb.connect()
    con.execute(f"CREATE TABLE txns AS SELECT * FROM read_csv_auto('{CSV_PATH}')")
    result = con.execute(sql).fetchdf()

    return {"sql": sql, "result": result}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Usage: python detective/ask_claude.py "your question here"')
        sys.exit(1)
    question = " ".join(sys.argv[1:])
    out = ask(question)
    print("\nGenerated SQL:\n" + out["sql"])
    print("\nResult:")
    print(out["result"].to_string(index=False))
