"""
AI-Powered Enterprise Data Detective -- Streamlit app.

A single screen where an analyst can:
  1. Load the transactions data (sample, or upload their own CSV)
  2. See an automatic data-quality profile
  3. See flagged suspicious transactions with reasons
  4. Ask questions in plain English (powered by Claude)

Run:  streamlit run app.py
"""

import os
import pandas as pd
import streamlit as st

from detective.profile_data import profile
from detective.detect_anomalies import detect

st.set_page_config(page_title="Enterprise Data Detective", layout="wide")
st.title("🕵️  AI-Powered Enterprise Data Detective")
st.caption("Profile, audit, and interrogate transaction data.")

# ---- Load data --------------------------------------------------------------
uploaded = st.file_uploader("Upload a transactions CSV (or use the sample)", type="csv")
if uploaded is not None:
    df = pd.read_csv(uploaded)
elif os.path.exists("data/transactions.csv"):
    df = pd.read_csv("data/transactions.csv")
    st.info("Using bundled sample data. Upload a CSV above to analyze your own.")
else:
    st.warning("No data found. Run: python data/generate_sample_data.py")
    st.stop()

tab1, tab2, tab3 = st.tabs(["📊 Profile", "🚩 Anomalies", "💬 Ask (AI)"])

# ---- Tab 1: profile ---------------------------------------------------------
with tab1:
    rep = profile(df)
    c1, c2, c3 = st.columns(3)
    c1.metric("Rows", f"{rep['rows']:,}")
    c2.metric("Columns", rep["columns"])
    c3.metric("Duplicate rows", rep["duplicate_rows"])
    st.dataframe(pd.DataFrame(rep["columns_detail"]), use_container_width=True)

# ---- Tab 2: anomalies -------------------------------------------------------
with tab2:
    flagged = detect(df)
    st.metric("Flagged transactions", f"{len(flagged)} of {len(df)}")
    cols = ["transaction_id", "account_id", "merchant", "amount",
            "country", "flag_reasons"]
    cols = [c for c in cols if c in flagged.columns]
    st.dataframe(flagged[cols], use_container_width=True)

# ---- Tab 3: natural-language Q&A -------------------------------------------
with tab3:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        st.warning("Set ANTHROPIC_API_KEY to enable AI questions.")
    question = st.text_input("Ask a question about the data",
                             placeholder="e.g. which 5 accounts spent the most?")
    if question:
        try:
            from detective.ask_claude import ask
            out = ask(question)
            st.code(out["sql"], language="sql")
            st.dataframe(out["result"], use_container_width=True)
        except Exception as e:
            st.error(f"Could not answer that: {e}")
