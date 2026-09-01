from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime


def say_hello():
    print("Hello from Airflow! The pipeline orchestration layer is working.")


with DAG(
    dag_id="hello_world",
    description="Minimal test DAG to confirm Airflow setup is working",
    start_date=datetime(2026, 8, 1),
    schedule=None,
    catchup=False,
    tags=["test"],
) as dag:

    hello_task = PythonOperator(
        task_id="say_hello",
        python_callable=say_hello,
    )