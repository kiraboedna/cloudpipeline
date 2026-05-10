import os
import json
import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine, text

engine = create_engine(
    f"postgresql+psycopg2://postgres:{os.getenv('PG_PASSWORD')}@localhost:5432/patents",
    pool_pre_ping=True
)

REPORTS_DIR = Path("reports")
REPORTS_DIR.mkdir(exist_ok=True)

sql = Path("sql/queries.sql").read_text(encoding="utf-8")

# Split queries by label
QUERY_LABELS = {
    "Q1": "Top Inventors",
    "Q2": "Top Companies",
    "Q3": "Countries",
    "Q4": "Trends Over Time",
    "Q5": "JOIN — Patents + Inventors + Companies",
    "Q6": "CTE — Top Companies per Country",
    "Q7": "Ranking — Inventors with Window Functions",
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
print("\n[QUERIES] Running Q1–Q7...")
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

# CSV exports
exports = {
    "top_inventors.csv":  ("Q1", 50),
    "top_companies.csv":  ("Q2", 50),
    "country_trends.csv": ("Q3", None),
    "yearly_trends.csv":  ("Q4", None),
    "inventor_ranks.csv": ("Q7", None),
}
print("\n[REPORTS] Exporting CSVs...")
for filename, (key, limit) in exports.items():
    df = results.get(key, pd.DataFrame())
    if df.empty:
        print(f"  ⚠ {filename}: no data")
        continue
    out = REPORTS_DIR / filename
    (df.head(limit) if limit else df).to_csv(out, index=False)
    print(f"  ✓ {out}")

# JSON report
with engine.connect() as conn:
    total = conn.execute(text("SELECT COUNT(*) FROM patent_details")).scalar()

def rows(key, fields, limit=20):
    df = results.get(key, pd.DataFrame())
    out = []
    for _, r in df.head(limit).iterrows():
        row = {}
        for src, dst in fields.items():
            val = r.get(src)
            row[dst] = int(val) if isinstance(val, float) and val.is_integer() else val
        out.append(row)
    return out

report = {
    "total_patents":  int(total),
    "top_inventors":  rows("Q1", {"inventor_name": "name", "country": "country", "patent_count": "patents"}),
    "top_companies":  rows("Q2", {"company_name": "name", "patent_count": "patents"}),
    "top_countries":  rows("Q3", {"country": "country", "patent_count": "patents", "pct_share": "share"}, limit=30),
    "yearly_trends":  rows("Q4", {"year": "year", "patents_filed": "patents_filed", "cumulative_total": "cumulative"}, limit=200),
}

out = REPORTS_DIR / "patent_report.json"
out.write_text(json.dumps(report, indent=2, ensure_ascii=False))
print(f"  ✓ {out}")
print("\n🎉 Reports done")