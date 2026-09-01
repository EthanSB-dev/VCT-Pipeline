"""
VCT extraction DAG.

Orchestrates the existing extract/extract_matches.py pipeline: pulls the
PandaScore API key from Airflow's Connection store (never from a local
.env file, since the Airflow containers don't have one), runs the
extraction, and logs a short summary of the result.
"""
import sys
import os
from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.hooks.base import BaseHook

sys.path.insert(0, "/opt/airflow/extract")


def run_extraction(**context):
    from pandascore_client import PandaScoreClient
    import extract_matches

    conn = BaseHook.get_connection("pandascore_api")
    api_key = conn.password

    extract_matches.client_override = PandaScoreClient(api_key=api_key)

    original_client_cls = extract_matches.PandaScoreClient
    extract_matches.PandaScoreClient = lambda: PandaScoreClient(api_key=api_key)

    try:
        extract_matches.extract_new_matches()
    finally:
        extract_matches.PandaScoreClient = original_client_cls

    context["ti"].xcom_push(key="run_completed_at", value=datetime.utcnow().isoformat())


def log_summary(**context):
    completed_at = context["ti"].xcom_pull(key="run_completed_at", task_ids="run_extraction")
    print(f"VCT extraction task finished. Completed at: {completed_at}")


with DAG(
    dag_id="vct_extraction",
    description="Extract new flagship VCT matches from PandaScore",
    start_date=datetime(2026, 8, 1),
    schedule=None,
    catchup=False,
    tags=["vct", "extraction"],
) as dag:

    extract_task = PythonOperator(
        task_id="run_extraction",
        python_callable=run_extraction,
    )

    summary_task = PythonOperator(
        task_id="log_summary",
        python_callable=log_summary,
    )

    extract_task >> summary_task