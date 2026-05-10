import os
import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine

engine = create_engine(
    f"postgresql+psycopg2://postgres:{os.getenv('PG_PASSWORD')}@localhost:5432/patents",
    pool_pre_ping=True
)

REPORTS_DIR = Path("reports")
REPORTS_DIR.mkdir(exist_ok=True)

sql = Path("sql/deep_queries.sql").read_text(encoding="utf-8")

QUERY_LABELS = {
    "D1": "Top 5 Inventors per Country",
    "D2": "Patent Type Breakdown",
    "D3": "Tech Trends by Year and Type",
    "D4": "Most Prolific Countries by Decade",
    "D5": "Top Companies by Patent Type",
    "D6": "Inventor Collaboration",
    "D7": "Average Claims by Patent Type",
    "D8": "Withdrawn Patents by Country",
}

queries = {}
current_key, current_lines = None, []
for line in sql.splitlines():
    for key in QUERY_LABELS:
        if line.strip().startswith(f"-- {key}:"):
            if current_key:
                queries[current_key] = "\n".join(current_lines).strip()
            current_key, current_lines = key, []
            break
    else:
        if current_key:
            current_lines.append(line)
if current_key:
    queries[current_key] = "\n".join(current_lines).strip()

results = {}
print("\n[DEEP QUERIES] Running D1–D8...")
for key, label in QUERY_LABELS.items():
    q = queries.get(key, "")
    if not q:
        print(f"  [{key}] ⚠ not found")
        continue
    try:
        print(f"  [{key}] {label} ... ", end="", flush=True)
        df = pd.read_sql(q, engine)
        results[key] = df
        print(f"{len(df):,} rows")
    except Exception as e:
        print(f"ERROR: {e}")

exports = {
    "top_inventors_per_country.csv": "D1",
    "patent_type_breakdown.csv":     "D2",
    "tech_trends_by_year.csv":       "D3",
    "countries_by_decade.csv":       "D4",
    "top_companies_by_type.csv":     "D5",
    "inventor_collaboration.csv":    "D6",
    "claims_by_type.csv":            "D7",
    "withdrawn_by_country.csv":      "D8",
}

print("\n[REPORTS] Exporting CSVs...")
for filename, key in exports.items():
    df = results.get(key, pd.DataFrame())
    if df.empty:
        print(f"  ⚠ {filename}: no data")
        continue
    out = REPORTS_DIR / filename
    df.to_csv(out, index=False)
    print(f"  ✓ {out}")

print("\n🎉 Deep queries done")