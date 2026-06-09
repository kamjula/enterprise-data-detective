"""
Data profiler.

Given any CSV, produce a quick "health check": shape, column types,
missing values, duplicate rows, numeric stats, and date range. This is the
first thing an FDE does when handed an unfamiliar enterprise dataset.

Run:  python detective/profile_data.py data/transactions.csv
"""

import sys
import pandas as pd


def profile(df: pd.DataFrame) -> dict:
    """Return a dictionary describing the dataset."""
    report = {}
    report["rows"] = len(df)
    report["columns"] = len(df.columns)

    # Per-column summary: type, how many missing, how many unique
    col_summary = []
    for col in df.columns:
        col_summary.append({
            "column": col,
            "dtype": str(df[col].dtype),
            "missing": int(df[col].isna().sum()),
            "missing_pct": round(df[col].isna().mean() * 100, 1),
            "unique": int(df[col].nunique()),
        })
    report["columns_detail"] = col_summary

    # Fully duplicated rows
    report["duplicate_rows"] = int(df.duplicated().sum())

    # Numeric columns: basic stats
    numeric = df.select_dtypes("number")
    report["numeric_stats"] = (
        numeric.describe().round(2).to_dict() if not numeric.empty else {}
    )

    # If there's a timestamp column, report the date range
    for col in df.columns:
        if "date" in col.lower() or "time" in col.lower():
            parsed = pd.to_datetime(df[col], errors="coerce")
            if parsed.notna().any():
                report["date_range"] = {
                    "column": col,
                    "min": str(parsed.min()),
                    "max": str(parsed.max()),
                }
            break
    return report


def print_report(report: dict) -> None:
    print(f"\n=== DATA PROFILE ===")
    print(f"Rows: {report['rows']:,}   Columns: {report['columns']}")
    print(f"Duplicate rows: {report['duplicate_rows']}")
    if "date_range" in report:
        d = report["date_range"]
        print(f"Date range ({d['column']}): {d['min']}  ->  {d['max']}")

    print("\nColumns:")
    print(f"{'name':<16}{'type':<12}{'missing':<14}{'unique':<8}")
    for c in report["columns_detail"]:
        miss = f"{c['missing']} ({c['missing_pct']}%)"
        print(f"{c['column']:<16}{c['dtype']:<12}{miss:<14}{c['unique']:<8}")


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "data/transactions.csv"
    df = pd.read_csv(path)
    print_report(profile(df))
