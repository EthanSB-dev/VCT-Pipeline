"""
VCT extraction + load DAG.

Orchestrates the full extract -> load flow:
1. Pull new flagship VCT matches from PandaScore (extract/extract_matches.py)
2. Load the resulting raw JSON files into the raw_matches Postgres table
   (load/load_matches.py), using an ELT pattern -- no parsing/transforming
   happens here, that's dbt's job in a later stage.

Credentials for both PandaScore and Postgres are resolved from Airflow
Connections at runtime, never from local .env files (the containers don't
have one) and never hardcoded in this file.
"""
import sys
from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.hooks.base import BaseHook

sys.path.insert(0, "/opt/airflow/extract")
sys.path.insert(0, "/opt/airflow/load")


def run_extraction(**context):
    from pandascore_client import PandaScoreClient
    import extract_matches

    conn = BaseHook.get_connection("pandascore_api")
    api_key = conn.password

    original_client_cls = extract_matches.PandaScoreClient
    extract_matches.PandaScoreClient = lambda: PandaScoreClient(api_key=api_key)

    try:
        extract_matches.extract_new_matches()
    finally:
        extract_matches.PandaScoreClient = original_client_cls

    context["ti"].xcom_push(key="run_completed_at", value=datetime.utcnow().isoformat())


def run_load(**context):
    import load_matches

    conn = BaseHook.get_connection("vct_warehouse")
    conn_uri = conn.get_uri()

    load_matches.load_all_raw_matches(conn_uri=conn_uri)

    context["ti"].xcom_push(key="load_completed_at", value=datetime.utcnow().isoformat())


def log_summary(**context):
    extracted_at = context["ti"].xcom_pull(key="run_completed_at", task_ids="run_extraction")
    loaded_at = context["ti"].xcom_pull(key="load_completed_at", task_ids="run_load")
    print(f"Extraction finished at: {extracted_at}")
    print(f"Load finished at: {loaded_at}")


with DAG(
    dag_id="vct_extraction",
    description="Extract new flagship VCT matches from PandaScore and load into Postgres",
    start_date=datetime(2026, 8, 1),
    schedule=None,
    catchup=False,
    tags=["vct", "extraction", "load"],
) as dag:

    extract_task = PythonOperator(
        task_id="run_extraction",
        python_callable=run_extraction,
    )

    load_task = PythonOperator(
        task_id="run_load",
        python_callable=run_load,
    )

    summary_task = PythonOperator(
        task_id="log_summary",
        python_callable=log_summary,
    )

    extract_task >> load_task >> summary_task