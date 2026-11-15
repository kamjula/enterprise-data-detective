# Enterprise Data Detective — application folder

This folder holds the runnable Streamlit app. Features, design notes, and limitations are in the [main README](../README.md).

```bash
pip install -r requirements.txt
python data/generate_sample_data.py
streamlit run app.py
```

Set `ANTHROPIC_API_KEY` to enable the natural-language Q&A tab. The modules can also be run on their own:

```bash
python detective/profile_data.py data/transactions.csv
python detective/detect_anomalies.py data/transactions.csv
python detective/ask_claude.py "top 5 merchants by total spend"
```
