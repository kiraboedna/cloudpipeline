import argparse
import os
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text
from tqdm import tqdm


# ─────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────

CHUNK_SIZE = 50_000
SQL_DIR = Path("sql")

DB_CONFIG = {
    "host": os.getenv("PG_HOST", "localhost"),
    "port": os.getenv("PG_PORT", "5432"),
    "db":   os.getenv("PG_DB", "patents"),
    "user": os.getenv("PG_USER", "postgres"),
    "pw":   os.getenv("PG_PASSWORD", "postgres"),
}


# ─────────────────────────────────────────────────────────────
# DB
# ─────────────────────────────────────────────────────────────

def get_engine():
    url = f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['pw']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['db']}"
    return create_engine(url, pool_pre_ping=True)


# ─────────────────────────────────────────────────────────────
# SCHEMA
# ─────────────────────────────────────────────────────────────

def create_schema(engine):
    print("\n[SCHEMA] Creating tables...")
    sql = (SQL_DIR / "schema.sql").read_text(encoding="utf-8", errors="ignore")
    with engine.begin() as conn:
        conn.execute(text(sql))
    print("[SCHEMA] Done.")


# ─────────────────────────────────────────────────────────────
# LOADERS
# ─────────────────────────────────────────────────────────────

def load_locations(engine, data_dir):
    file = data_dir / "g_location_disambiguated_cleaned.csv"
    if not file.exists():
        print("⚠ locations file missing")
        return

    reader = pd.read_csv(file, sep="\t", chunksize=CHUNK_SIZE, dtype=str)

    total = 0

    with engine.begin() as conn:

        # TEMP TABLE
        conn.execute(text("""
            CREATE TEMP TABLE tmp_locations (
                location_id TEXT,
                city TEXT,
                state TEXT,
                country TEXT,
                county TEXT
            ) ON COMMIT DROP;
        """))

        for chunk in tqdm(reader, desc="locations"):

            chunk = chunk.rename(columns={
                "location_id": "location_id",
                "disambig_city": "city",
                "disambig_state": "state",
                "disambig_country": "country",
                "county": "county",
            })

            chunk = chunk.where(pd.notna(chunk), None)

            chunk.to_sql("tmp_locations", conn, if_exists="append", index=False)
            total += len(chunk)

        # UPSERT SAFE INSERT
        conn.execute(text("""
            INSERT INTO locations (location_id, city, state, country, county)
            SELECT DISTINCT location_id, city, state, country, county
            FROM tmp_locations
            WHERE location_id IS NOT NULL
            ON CONFLICT (location_id) DO NOTHING
        """))

    print(f"✓ locations (deduplicated): {total:,}")


def load_patents(engine, data_dir):
    file = data_dir / "g_patent_abstract_cleaned.csv"
    if not file.exists():
        print("⚠ patents file missing")
        return

    total = 0
    for chunk in tqdm(pd.read_csv(file, sep="\t", chunksize=CHUNK_SIZE, dtype=str)):
        chunk = chunk.rename(columns={
            "patent_id": "patent_id",
            "patent_abstract": "abstract",
        })

        chunk = chunk.dropna(subset=["patent_id"])
        chunk = chunk.where(pd.notna(chunk), None)

        chunk.to_sql("patents", engine, if_exists="append", index=False)
        total += len(chunk)

    print(f"✓ patents: {total:,}")


def load_patent_details(engine, data_dir):
    file = data_dir / "g_patent_cleaned.csv"
    if not file.exists():
        print("⚠ g_patent_cleaned.csv missing")
        return

    total = 0
    with engine.begin() as conn:

        # Temp table to stage everything
        conn.execute(text("""
            CREATE TEMP TABLE tmp_pd (
                patent_id   TEXT,
                patent_type TEXT,
                patent_date TEXT,
                patent_title TEXT,
                wipo_kind   TEXT,
                num_claims  TEXT,
                withdrawn   TEXT,
                filename    TEXT
            ) ON COMMIT DROP;
        """))

        for chunk in tqdm(pd.read_csv(file, sep="\t", chunksize=50_000, dtype=str),
                          desc="patent_details"):

            chunk = chunk.replace({"": None, "unknown": None})
            chunk = chunk.dropna(subset=["patent_id"])
            chunk.to_sql("tmp_pd", conn, if_exists="append", index=False)
            total += len(chunk)

        print(f"  staged {total:,} rows — inserting...")

        # Insert any patent_ids not yet in patents table
        conn.execute(text("""
            INSERT INTO patents (patent_id)
            SELECT DISTINCT patent_id FROM tmp_pd
            ON CONFLICT (patent_id) DO NOTHING;
        """))

        # Insert details, casting types in SQL
        conn.execute(text("""
            INSERT INTO patent_details (
                patent_id, patent_type, patent_date, patent_title,
                wipo_kind, num_claims, withdrawn, filename
            )
            SELECT
                patent_id,
                patent_type,
                patent_date::DATE,
                patent_title,
                wipo_kind,
                num_claims::INT,
                CASE withdrawn
                    WHEN '1' THEN TRUE
                    WHEN '0' THEN FALSE
                    WHEN 'true'  THEN TRUE
                    WHEN 'false' THEN FALSE
                    ELSE NULL
                END,
                filename
            FROM tmp_pd
            ON CONFLICT (patent_id) DO NOTHING;
        """))

    print(f"✓ patent_details: {total:,}")

# ─────────────────────────────────────────────────────────────
# 🔥 INVENTORS (FIXED PROPERLY)
# ─────────────────────────────────────────────────────────────

def load_inventors(engine, data_dir):
    file = data_dir / "g_inventor_disambiguated_cleaned.csv"
    if not file.exists():
        print("⚠ inventors file missing")
        return

    reader = pd.read_csv(file, sep="\t", chunksize=CHUNK_SIZE, dtype=str)

    inv_seen = set()
    total_inv = 0

    with engine.begin() as conn:

        conn.execute(text("""
            CREATE TEMP TABLE tmp_pi (
                patent_id TEXT,
                inventor_id TEXT,
                sequence INT
            ) ON COMMIT DROP;
        """))

        for chunk in tqdm(reader, desc="inventors"):

            chunk = chunk.rename(columns={
                "patent_id": "patent_id",
                "inventor_id": "inventor_id",
                "inventor_sequence": "sequence",
                "disambig_inventor_name_first": "first",
                "disambig_inventor_name_last": "last",
                "gender_code": "gender",
                "location_id": "location_id"
            })

            chunk = chunk.replace({"": None, "unknown": None})

            # INVENTORS TABLE
            chunk["full_name"] = (
                chunk["first"].fillna("") + " " + chunk["last"].fillna("")
            ).str.strip()

            inv = chunk[[
                "inventor_id", "first", "last",
                "full_name", "gender", "location_id"
            ]].rename(columns={
                "first": "name_first",
                "last": "name_last",
                "gender": "gender_code"
            }).drop_duplicates("inventor_id")

            new_inv = inv[~inv["inventor_id"].isin(inv_seen)]

            if not new_inv.empty:
                new_inv.to_sql("inventors", conn, if_exists="append", index=False)
                inv_seen.update(new_inv["inventor_id"])
                total_inv += len(new_inv)

            # STAGING RELATION
            pi = chunk[["patent_id", "inventor_id", "sequence"]].copy()
            pi["sequence"] = pd.to_numeric(pi["sequence"], errors="coerce")
            pi = pi.dropna(subset=["patent_id", "inventor_id"])

            pi.to_sql("tmp_pi", conn, if_exists="append", index=False)

        # FINAL INSERT (FK SAFE)
        conn.execute(text("""
            INSERT INTO patent_inventor (patent_id, inventor_id, sequence)
            SELECT t.patent_id, t.inventor_id, t.sequence
            FROM tmp_pi t
            JOIN patents p ON p.patent_id = t.patent_id
            ON CONFLICT DO NOTHING
        """))

    print(f"✓ inventors: {total_inv:,}")
    print("✓ patent_inventor loaded (FK-safe)")


# ─────────────────────────────────────────────────────────────
# 🔥 ASSIGNEES (FIXED SAME WAY)
# ─────────────────────────────────────────────────────────────

def load_assignees(engine, data_dir):
    file = data_dir / "g_assignee_disambiguated_cleaned.csv"
    if not file.exists():
        print("⚠ assignees file missing")
        return

    reader = pd.read_csv(file, sep="\t", chunksize=CHUNK_SIZE, dtype=str)

    comp_seen = set()
    total_comp = 0

    with engine.begin() as conn:

        conn.execute(text("""
            CREATE TEMP TABLE tmp_pa (
                patent_id TEXT,
                company_id TEXT,
                sequence INT
            ) ON COMMIT DROP;
        """))

        for chunk in tqdm(reader, desc="assignees"):

            chunk = chunk.rename(columns={
                "patent_id": "patent_id",
                "assignee_id": "company_id",
                "assignee_sequence": "sequence",
                "disambig_assignee_organization": "org",
                "disambig_assignee_individual_name_first": "first",
                "disambig_assignee_individual_name_last": "last",
                "assignee_type": "type",
                "location_id": "location_id"
            })

            chunk = chunk.replace({"": None, "unknown": None})

            chunk["name"] = chunk["org"].where(
                chunk["org"].notna(),
                (chunk["first"].fillna("") + " " + chunk["last"].fillna("")).str.strip()
            )

            comp = chunk[[
                "company_id", "name", "type", "location_id"
            ]].drop_duplicates("company_id")

            new_comp = comp[~comp["company_id"].isin(comp_seen)]

            if not new_comp.empty:
                new_comp.to_sql("companies", conn, if_exists="append", index=False)
                comp_seen.update(new_comp["company_id"])
                total_comp += len(new_comp)

            pa = chunk[["patent_id", "company_id", "sequence"]].copy()
            pa["sequence"] = pd.to_numeric(pa["sequence"], errors="coerce")
            pa = pa.dropna(subset=["patent_id", "company_id"])

            pa.to_sql("tmp_pa", conn, if_exists="append", index=False)

        conn.execute(text("""
            INSERT INTO patent_assignee (patent_id, company_id, sequence)
            SELECT t.patent_id, t.company_id, t.sequence
            FROM tmp_pa t
            JOIN patents p ON p.patent_id = t.patent_id
            ON CONFLICT DO NOTHING
        """))

    print(f"✓ companies: {total_comp:,}")
    print("✓ patent_assignee loaded (FK-safe)")


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────

def table_empty(engine, table):
    with engine.connect() as conn:
        return conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar() == 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data")
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    print("\n══ Patent Pipeline ══")

    try:
        engine = get_engine()
        with engine.connect() as c:
            c.execute(text("SELECT 1"))
        print("✅ DB connected")
    except Exception as e:
        sys.exit(f"❌ DB failed: {e}")

    create_schema(engine)

    data_dir = Path(args.data)

    load_locations(engine, data_dir)
    load_patents(engine, data_dir)
    if not args.resume or table_empty(engine, "inventors"):
        load_inventors(engine, data_dir)
    if not args.resume or table_empty(engine, "companies"):
        load_assignees(engine, data_dir)
    if not args.resume or table_empty(engine, "patent_details"):
        load_patent_details(engine, data_dir)
    

    print("\n🎉 DONE")


if __name__ == "__main__":
    main()