# Data Engineering ETL (Airflow + PostgreSQL)

Simple, step-by-step instructions to get this project running locally or with Docker.

What this repo contains

- ETL code to process NVIDIA stock data and an example `employee` ETL DAG
- Airflow DAGs in the `dags/` folder
- A small Streamlit dashboard in `web/main.py` that reads from PostgreSQL

Quick overview

- Use Docker to run PostgreSQL + pgAdmin (fast)
- Run Airflow locally for development (LocalExecutor)
- Use Streamlit to view the processed data

Prerequisites

- Python 3.12+
- Docker & Docker Compose (optional but recommended)
- (Optional) `uv` package manager if you already use it; otherwise `pip` works

1. Clone

```bash
git clone <repo-url>
cd Data-Engineering
```

2. Start database (Docker)

This project includes a Docker Compose file to run PostgreSQL and pgAdmin:

```bash
docker compose -f docker/docker-compose.yml up -d
```

- PostgreSQL will be available on port `1234` (container name: `postgres_de`).
- pgAdmin will be available on http://localhost:6969 (email: `admin@gmail.com`, password: `admin123`).

3. Configure environment variables

Create a `.env` file in the project root (example):

```env
# database
DB_HOST=localhost
DB_PORT=1234
DB_NAME=etl_db
DB_USER=postgres
DB_PASS=admin123
TABLE_NAME=employees

# (optional) airflow settings can be left as defaults for local runs
```

4. Install Python dependencies (local development)

Option A — if you use `uv` (project was tested with uv):

```bash
uv sync
```

Option B — standard Python venv + pip:

```bash
python -m venv .venv
# macOS / Linux
source .venv/bin/activate
# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1
# Install project (uses pyproject.toml)
pip install -e .
```

5. Initialize and run Airflow (local)

Set executor and initialize the metadata database, then create an admin user:

```bash
export AIRFLOW__CORE__EXECUTOR=LocalExecutor   # macOS / Linux
setx AIRFLOW__CORE__EXECUTOR LocalExecutor      # Windows (PowerShell)
airflow db init
airflow users create --username admin --password admin --role Admin --email admin@example.com
```

Start the UI and scheduler in separate terminals:

```bash
airflow webserver --port 8080
airflow scheduler
```

Open http://localhost:8080 and sign in with the admin user you created.

FAQ — Reset or regenerate the Airflow admin password

- Easiest: re-run the users create command with the same username and new password:

```bash
airflow users create --username admin --password NEW_PASSWORD --role Admin --email admin@example.com
```

If that doesn't update the password (older Airflow versions) you can manually update the user in the Airflow metadata database (Postgres) or recreate the user after resetting the DB — note this is destructive.

6. Run the ETL DAGs

- Place or update CSV files in `database/` or configure `CSV_PATH` env var.
- From the Airflow UI enable the DAG(s) found in `dags/` and trigger runs manually to test.

7. Run the Streamlit dashboard

```bash
# ensure .env is set or environment variables are exported
streamlit run web/main.py
```

Notes & troubleshooting

- If Airflow cannot connect to Postgres, confirm `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASS`, and `DB_NAME` are correct.
- The included `docker/docker-compose.yml` only starts Postgres and pgAdmin. Airflow is run locally via the `airflow` command in this README.
- If dependencies fail to install via `pip install -e .` try creating a minimal `requirements.txt` for your environment.

Project structure (high level)

```
.
├── dags/                # Airflow DAGs
├── database/            # Sample CSVs and helpers
├── docker/              # docker-compose for Postgres + pgAdmin
├── web/                 # Streamlit dashboard
├── src/                 # ETL application code
├── Dockerfile
└── pyproject.toml       # Python packaging / dependencies
```

If you want, I can also:

- add a `requirements.txt` for simpler installs
- provide a small docker-compose that includes Airflow containers
- or demonstrate resetting the Airflow admin password more safely using SQL (if needed)

Made with ❤️
