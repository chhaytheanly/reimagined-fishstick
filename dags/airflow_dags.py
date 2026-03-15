from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from datetime import datetime, timedelta
import pandas as pd
from src.app.utils.logger import logger
from src.main import ETL
from database.path import input_data, output_data

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2024, 1, 1),
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}


etl = ETL(input_data)


def extract_task(**context):
    logger.info("Running extract task")
    df = etl.extract()
    context["ti"].xcom_push(key="data", value=df.to_json())


def clean_task(**context):
    logger.info("Running clean task")
    ti = context["ti"]

    df = ti.xcom_pull(key="data")
    df = ETL(input_data).clean_data(
        pd.read_json(df)
    )

    ti.xcom_push(key="data", value=df.to_json())


def transform_task(**context):
    logger.info("Running transform task")

    ti = context["ti"]

    df = ti.xcom_pull(key="data")
    df = pd.read_json(df)

    df = etl.transform(df)

    ti.xcom_push(key="data", value=df.to_json())


def load_task(**context):
    logger.info("Running load task")

    ti = context["ti"]

    df = ti.xcom_pull(key="data")
    df = pd.read_json(df)

    etl.load_to_file(df, str(output_data))
    etl.load_to_db(df)


with DAG(
    dag_id="nvidia_stock_etl_pipeline",
    default_args=default_args,
    description="ETL pipeline for NVIDIA stock dataset",
    schedule="@daily",
    catchup=False,
) as dag:

    extract = PythonOperator(
        task_id="extract",
        python_callable=extract_task
    )

    clean = PythonOperator(
        task_id="clean",
        python_callable=clean_task
    )

    transform = PythonOperator(
        task_id="transform",
        python_callable=transform_task
    )

    load = PythonOperator(
        task_id="load",
        python_callable=load_task
    )

    extract >> clean >> transform >> load