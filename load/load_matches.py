"""
Load raw VCT match JSON files into the raw_matches Postgres table.

ELT pattern: stores each PandaScore match payload as-is in a jsonb column.
No parsing/transforming happens here — that's dbt's job in a later stage.
"""
import glob
import json
import os

import psycopg2
from psycopg2.extras import execute_values

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS raw_matches (
    id SERIAL PRIMARY KEY,
    match_id BIGINT UNIQUE NOT NULL,
    raw_payload JSONB NOT NULL,
    loaded_at TIMESTAMPTZ DEFAULT now()
);
"""

UPSERT_SQL = """
INSERT INTO raw_matches (match_id, raw_payload)
VALUES %s
ON CONFLICT (match_id) DO UPDATE
SET raw_payload = EXCLUDED.raw_payload,
    loaded_at = now();
"""


def load_all_raw_matches(conn_uri: str) -> None:
    """
    Reads every matches_*.json file in data/raw/ and upserts each match
    into the raw_matches table, keyed on PandaScore's match id. Safe to
    rerun: existing matches get their payload refreshed rather than
    duplicated.
    """
    files = sorted(glob.glob(os.path.join(RAW_DIR, "matches_*.json")))
    if not files:
        print("No raw match files found. Nothing to load.")
        return

    conn = psycopg2.connect(conn_uri)
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(CREATE_TABLE_SQL)

        total_loaded = 0
        for path in files:
            with open(path) as f:
                matches = json.load(f)

            if not matches:
                print(f"{os.path.basename(path)} is empty, skipping.")
                continue

            rows = [(m["id"], json.dumps(m)) for m in matches]

            with conn:
                with conn.cursor() as cur:
                    execute_values(cur, UPSERT_SQL, rows)

            total_loaded += len(rows)
            print(f"Loaded {len(rows)} matches from {os.path.basename(path)}")

        print(f"Done. Total matches upserted: {total_loaded}")
    finally:
        conn.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python load_matches.py <postgres_conn_uri>")
        sys.exit(1)

    load_all_raw_matches(conn_uri=sys.argv[1])