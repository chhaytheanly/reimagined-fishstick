import sqlalchemy
from datetime import datetime, timedelta
from airflow import DAG
from airflow.decorators import task
from airflow.exceptions import AirflowException
import pandas as pd
import json
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import os

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "1234")
DB_NAME = os.getenv("DB_NAME", "etl_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "admin123")
CSV_PATH = os.getenv("CSV_PATH", "/home/eugene/airflow/database/employees.csv")
TABLE_NAME = os.getenv("TABLE_NAME", "employees")

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

DEFAULT_ARGS = {
    "owner": "data_team",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=3),
    "execution_timeout": timedelta(minutes=15),
}

log = logging.getLogger(__name__)

with DAG(
    dag_id="employee_etl_postgres",
    default_args=DEFAULT_ARGS,
    description="ETL: Employee CSV → PostgreSQL with SQLAlchemy",
    schedule="@daily",  
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["production", "etl", "hr", "postgres"],
    max_active_runs=1,
) as dag:

    @task(task_id="extract")
    def extract() -> str:
        try:
            if not os.path.exists(CSV_PATH):
                raise FileNotFoundError(f"CSV not found: {CSV_PATH}")
            df = pd.read_csv(CSV_PATH, dtype=str, encoding="utf-8", on_bad_lines="skip")
            log.info(f"✓ Extracted {len(df)} rows from {CSV_PATH}")

            return df.to_json(orient="records", force_ascii=False)
        except Exception as e:
            log.error(f"✗ Extract failed: {e}")
            raise AirflowException(f"Extract task failed: {e}")

    @task(task_id="transform")
    def transform(raw_json: str) -> str:
        try:
            data = json.loads(raw_json)
            df = pd.DataFrame(data)

            df["first_name"] = df["First Name"].str.strip().fillna("Unknown")
            df["gender"] = df["Gender"].str.strip().fillna("Unknown")
            df["team"] = df["Team"].str.strip().fillna("Unassigned")
            df["senior_management"] = (
                df["Senior Management"]
                .astype(str)
                .str.lower()
                .isin(["true", "1", "yes", "t"])
            )

            df["start_date"] = pd.to_datetime(df["Start Date"], errors="coerce", dayfirst=False)
            df["last_login"] = pd.to_datetime(df["Last Login Time"], errors="coerce")
            df["salary"] = pd.to_numeric(df["Salary"], errors="coerce").fillna(0)
            df["bonus_pct"] = pd.to_numeric(df["Bonus %"], errors="coerce").fillna(0.0)
            df["bonus_amount"] = (df["salary"] * df["bonus_pct"] / 100).round(2)
            df["total_compensation"] = (df["salary"] + df["bonus_amount"]).round(2)

            df_final = df[[
                "first_name", "gender", "start_date", "last_login",
                "salary", "bonus_pct", "bonus_amount", "total_compensation",
                "senior_management", "team"
            ]].copy()

            initial_count = len(df_final)
            df_final = df_final.dropna(subset=["first_name", "salary"])
            dropped = initial_count - len(df_final)
            if dropped > 0:
                log.warning(f" Dropped {dropped} rows with missing critical fields")

            log.info(f"Transformed {len(df_final)} rows")
            return df_final.to_json(orient="records", date_format="iso", force_ascii=False)

        except Exception as e:
            log.error(f"✗ Transform failed: {e}")
            raise AirflowException(f"Transform task failed: {e}")

    @task(task_id="load")
    def load(transformed_json: str) -> bool:
        try:
            data = json.loads(transformed_json)
            df = pd.DataFrame(data)

            if df.empty:
                log.warning(" No data to load")
                return True

            engine = create_engine(
                DATABASE_URL,
                pool_pre_ping=True,          
                pool_recycle=3600,           
                connect_args={"connect_timeout": 10, "options": "-c timezone=utc"}
            )

            with engine.begin() as conn:
                conn.execute(text(f"""
                    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                        id SERIAL PRIMARY KEY,
                        first_name VARCHAR(100) NOT NULL,
                        gender VARCHAR(20),
                        start_date TIMESTAMP,
                        last_login TIMESTAMP,
                        salary NUMERIC(12,2) DEFAULT 0,
                        bonus_pct NUMERIC(5,3) DEFAULT 0,
                        bonus_amount NUMERIC(12,2),
                        total_compensation NUMERIC(12,2),
                        senior_management BOOLEAN DEFAULT FALSE,
                        team VARCHAR(100),
                        loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                conn.execute(text(f"""
                    CREATE INDEX IF NOT EXISTS idx_{TABLE_NAME}_first_name
                    ON {TABLE_NAME}(first_name)
                """))

            df.to_sql(
                TABLE_NAME,
                engine,
                if_exists="append",          
                index=False,
                method="multi",              
                chunksize=1000,
                dtype={
                    "first_name": sqlalchemy.types.String(100),
                    "gender": sqlalchemy.types.String(20),
                    "team": sqlalchemy.types.String(100),
                }
            )

            log.info(f" Loaded {len(df)} rows into {TABLE_NAME}")
            engine.dispose()  
            return True

        except SQLAlchemyError as e:
            log.error(f" Database error: {e}")
            raise AirflowException(f"Load task failed (DB): {e}")
        except Exception as e:
            log.error(f" Load failed: {e}")
            raise AirflowException(f"Load task failed: {e}")

    raw = extract()
    clean = transform(raw)
    load(clean)