# VCT Pipeline

An end-to-end data engineering pipeline that extracts flagship VALORANT Champions Tour (VCT) match data, loads it into Postgres, and transforms it into analytics-ready tables using Airflow and dbt.

Built to move beyond a one-off analysis notebook into a production-style, orchestrated pipeline: automated extraction, incremental loading, tested transformations, and scheduled runs — all containerized and reproducible from a single `docker compose up`.

## Architecture

```
PandaScore API  -->  Extract  -->  Raw JSON  -->  Load  -->  Postgres (raw_matches)  -->  dbt  -->  Marts
                     (Airflow)                  (Airflow)                              (Airflow)
```

The pipeline follows an ELT pattern:

1. **Extract** — Pulls new flagship VCT matches (EMEA, Pacific, China, Americas) from the PandaScore API, filtered to franchised tournament series only (Game Changers, Challengers, Ascension, and qualifiers are excluded).
2. **Load** — Loads the raw extracted JSON into a `raw_matches` table in Postgres, preserving the source payload for reprocessing.
3. **Transform** — dbt models transform `raw_matches` through staging and intermediate layers into mart tables: `fct_matches`, `dim_teams`, and `dim_tournaments`. dbt tests validate the output after every run.

All five steps are orchestrated as a single Airflow DAG (`vct_extraction`), running on a schedule with dependency-aware task ordering.

## Tech Stack

| Layer | Tool |
|---|---|
| Orchestration | Apache Airflow 2.9.3 |
| Extraction | Python, PandaScore API |
| Storage | PostgreSQL |
| Transformation | dbt-core 1.8.2 (dbt-postgres adapter) |
| Containerization | Docker Compose |

## Project Structure

```
vct-pipeline/
├── dags/
│   └── vct_extraction_dag.py     # Airflow DAG: extract -> load -> dbt run -> dbt test
├── extract/
│   ├── pandascore_client.py      # PandaScore API client
│   ├── extract_matches.py        # Extraction entrypoint
│   ├── vct_filters.py            # Flagship tournament filtering logic
│   └── checkpoint.py             # Tracks last successful extraction point
├── load/
│   └── load_matches.py           # Loads raw match JSON into Postgres
├── transform/
│   └── vct_dbt/                  # dbt project (models, tests, macros)
├── Dockerfile                    # Custom Airflow image with dbt installed
├── docker-compose.yml            # Airflow + Postgres services
└── .env.example                  # Required environment variables template
```

## Setup

**Prerequisites:** Docker Desktop, a PandaScore API key.

1. Clone the repo and copy the environment template:
   ```bash
   cp .env.example .env
   ```
   Fill in your PandaScore API key and Postgres credentials.

2. Build and start the stack:
   ```bash
   docker compose build
   docker compose up -d
   ```

3. In the Airflow UI (`localhost:8080`), add two connections:
   - `pandascore_api` — HTTP connection with your PandaScore API key as the password.
   - `vct_warehouse` — Postgres connection pointing at the warehouse database.

4. Trigger the DAG manually or wait for its schedule:
   ```bash
   docker compose exec airflow-webserver airflow dags trigger vct_extraction
   ```

## DAG Schedule

The `vct_extraction` DAG runs every 6 hours (`0 */6 * * *`), matching the cadence at which new flagship VCT matches are typically played and reported.

## A Note on dbt Versions

This project pins `dbt-core==1.8.2` and `dbt-postgres==1.8.2` explicitly in the Dockerfile. Installing `dbt-postgres` alone without pinning `dbt-core` will resolve to the latest `dbt-core` release, which as of 2026 is the new Rust-based **dbt Fusion** engine — and Fusion does not yet support the Postgres adapter. Pin both packages together to stay on the classic engine.

## Data Model

- **`fct_matches`** — One row per match: teams, tournament, map score, winner, timestamps.
- **`dim_teams`** — Team reference data.
- **`dim_tournaments`** — Flagship tournament metadata (region, stage, season).

## Roadmap

- [ ] Add failure alerting (email/Slack) on task failure.
- [ ] Backfill historical matches beyond the current extraction window.
- [ ] Deploy to AWS (MWAA or ECS + RDS) once the pipeline is stable.
- [ ] Add data quality dashboards on top of the marts layer.

## Background

This pipeline supports a VCT esports match outcome predictor originally built as an exploratory ML project (SVM, ~100K observations across VCT Kickoff and Masters Santiago). This repo represents the productionization of that data collection process into a maintainable, automated pipeline.
