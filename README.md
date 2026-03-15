# ETL Pipeline

A data engineering ETL pipeline for processing NVIDIA stock data, built with Python, Apache Airflow, and PostgreSQL.

## Features

- **Extract**: Load stock data from CSV files
- **Clean**: Remove duplicates, handle missing values, parse dates
- **Transform**: Feature engineering (daily returns, price ranges)
- **Load**: Export to CSV and PostgreSQL database
- **Orchestration**: Apache Airflow DAG for scheduled runs

## Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (package manager)
- PostgreSQL (for database loading)
- Docker & Docker Hub (for containerized deployment)

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd data_engineering
```

### 2. Install Dependencies

```bash
uv sync
```

### 3. Configure Environment

Create a `.env` file in the project root:

```env
# Database configuration
DATABASE_URL=postgresql://user:password@localhost:5432/your_database

# Docker Hub (for CI/CD)
DOCKERHUB_USERNAME=your_username
DOCKERHUB_TOKEN=your_token
```

## Usage

### Run ETL Pipeline Locally

```bash
uv run python src/main.py
```

### Run with Apache Airflow

1. **Initialize Airflow** (if running locally):
   ```bash
   export AIRFLOW__CORE__EXECUTOR=LocalExecutor
   airflow db init
   airflow users create --username admin --password admin --role Admin --email admin@example.com
   ```

2. **Start Airflow**:
   ```bash
   airflow webserver --port 8080
   airflow scheduler
   ```

3. **Access the DAG**:
   - Open http://localhost:8080
   - Enable the `nvidia_stock_etl_pipeline` DAG
   - The DAG runs daily at midnight

### Run with Docker

```bash
# Build the image
docker build -t data-engineering:latest .

# Run the container
docker run --env-file .env data-engineering:latest
```

## Project Structure

```
data_engineering/
├── src/
│   ├── main.py              # ETL pipeline implementation
│   └── app/
│       ├── config/          # Configuration files
│       └── utils/           # Utility functions (logger, etc.)
├── dags/
│   └── airflow_dags.py      # Airflow DAG definitions
├── database/
│   ├── nvidia_stock_data_1999_2026.csv    # Raw input data
│   ├── cleaned_nvidia_stock_data_1999_2026.csv  # Processed output
│   └── path.py              # Path configurations
├── Dockerfile               # Container image definition
├── pyproject.toml           # Project dependencies
└── .github/workflows/
    └── docker-build.yml     # CI/CD pipeline
```

## ETL Pipeline Details

### Extract
- Reads NVIDIA stock data from CSV
- Validates file existence and data presence

### Clean
- Removes duplicate rows
- Converts date column to datetime
- Fills missing stock split values

### Transform
- Converts numeric columns safely
- Sorts by date (time-series order)
- Generates features:
  - `daily_return`: Percentage change in closing price
  - `price_range`: High - Low price difference

### Load
- Saves cleaned data to CSV
- Loads data into PostgreSQL table `nvidia_stock_data`

## CI/CD Pipeline

The GitHub Actions workflow automatically builds and pushes Docker images to Docker Hub when tags are pushed.

### Trigger a Build

```bash
git tag v1.0.0
git push origin v1.0.0
```

This creates images with tags:
- `v1.0.0` (full version)
- `v1.0` (major.minor)
- `v1` (major)

### Required GitHub Secrets

| Secret | Description |
|--------|-------------|
| `DOCKERHUB_USERNAME` | Your Docker Hub username |
| `DOCKERHUB_TOKEN` | Docker Hub access token |

## Data

The pipeline processes NVIDIA stock data including:
- OHLCV data (Open, High, Low, Close, Volume)
- Market metrics (market cap, shares outstanding)
- Technical indicators (SMA 20/50/200, RSI 14)
- Stock split information

## Writer

The cleaned and transformed data is written to:
- A new CSV file: `cleaned_nvidia_stock_data_1999_2026
- A PostgreSQL database table: `nvidia_stock_data`

Made with ❤️ by Chhaythean LY

## License

MIT
