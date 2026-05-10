GitHub repo link: https://github.com/kiraboedna/cloudpipeline.git

Dashboard link: https://kiraboedna.github.io/cloudpipeline/

Reports link: https://github.com/kiraboedna/cloudpipeline/tree/main/reports

# Global Patent Intelligence Data Pipeline

Handles 1–5 GB PatentsView CSV files, loads them into PostgreSQL in chunks,
runs 7 analytical SQL queries, and produces console, CSV, and JSON reports.

---

## Project Structure

```
patent_pipeline/
├── data/                                          ← Put your CSV files here
│   ├── g_patent_abstract_cleaned.csv
│   ├── g_inventor_disambiguated_cleaned.csv
│   ├── g_assignee_disambiguated_cleaned.csv
│   └── g_location_disambiguated_cleaned.csv
├── sql/
│   ├── schema.sql                                 ← Table definitions
│   └── queries.sql                                ← Q1–Q7 queries
├── reports/                                       ← Auto-created on first run
│   ├── top_inventors.csv
│   ├── top_companies.csv
│   ├── country_trends.csv
│   ├── yearly_trends.csv
│   ├── inventor_ranks.csv
│   └── patent_report.json
├── pipeline.py                                    ← Main script
└── README.md
```

---

## CSV → Database Column Mapping

| CSV File | CSV Columns Used | DB Table |
|---|---|---|
| g_location_disambiguated_cleaned.csv | location_id, disambig_city, disambig_state, disambig_country, county | locations |
| g_patent_abstract_cleaned.csv | patent_id, patent_abstract | patents |
| g_inventor_disambiguated_cleaned.csv | patent_id, inventor_sequence, inventor_id, disambig_inventor_name_first, disambig_inventor_name_last, gender_code, location_id | inventors + patent_inventor |
| g_assignee_disambiguated_cleaned.csv | patent_id, assignee_sequence, assignee_id, disambig_assignee_organization, disambig_assignee_individual_name_first/last, assignee_type, location_id | companies + patent_assignee |

The inventor and assignee files each serve double duty — unique inventors/companies
go into their own tables, and every patent↔person row goes into the relationship table.

---

## Setup

### 1. Install dependencies
```bash
pip install pandas psycopg2-binary sqlalchemy tqdm
```

### 2. Create your PostgreSQL database
```sql
CREATE DATABASE patents;
```

### 3. Set environment variables
```bash
export PG_HOST=localhost
export PG_PORT=5432
export PG_DB=patents
export PG_USER=postgres
export PG_PASSWORD=your_password
```

### 4. Place your cleaned CSV files in `data/`

---

## Running

```bash
# Full run — load all CSVs then generate reports
python pipeline.py

# Custom data folder
python pipeline.py --data /path/to/your/csvs

# Skip loading (re-run queries and reports only)
python pipeline.py --skip-load
```

---

## SQL Queries (Q1–Q7)

| Query | Description |
|---|---|
| Q1 | Top inventors by patent count |
| Q2 | Top companies/assignees by patent count |
| Q3 | Countries ranked by patent output + % share |
| Q4 | Patents per year + cumulative total (derived from patent_id) |
| Q5 | JOIN — patents with lead inventor and assignee |
| Q6 | CTE — top 5 companies per country |
| Q7 | Window functions — global rank + country rank per inventor |

---

## Performance Notes (large files)

- Files are read in **50,000-row chunks** — memory stays low even for 5 GB files
- Only the columns needed for each table are read (`usecols`) — faster I/O
- Inventors and assignees are **deduplicated in-memory** across chunks before insert
- Indexes are created after loading for faster query performance

## Limitations 
The clean data files (dean_patents.csv, dean_inventors.csv and dean_companies.csv) couldnot be uploaded to GitHub due to file size contraints and limits exceeding GitHub's maximum upload threshold.The data was however processed and results are reflected in the dashboard and console report.
