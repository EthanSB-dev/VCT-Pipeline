FROM apache/airflow:2.9.3

USER airflow

RUN pip install --no-cache-dir "dbt-core==1.8.2" "dbt-postgres==1.8.2"