import pandas as pd
from pathlib import Path
from src.app.utils.logger import logger
from src.app.config.config import engine
from database.path import input_data, output_data

class ETL:
    def __init__(self, input_path: Path):
        self.input_path = Path(input_path).resolve()

    def extract(self) -> pd.DataFrame:
        logger.info("Extracting data from CSV...")

        if not self.input_path.exists():
            raise FileNotFoundError(f"Input file not found: {self.input_path}")

        df = pd.read_csv(self.input_path)

        if df.empty:
            raise ValueError("Extracted dataset is empty")

        logger.info(f"Data extracted successfully. Rows: {len(df)}")
        return df

    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        logger.info("Cleaning data...")

        df = df.drop_duplicates().copy()

        # Convert date column
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

        # Remove invalid dates
        df = df.dropna(subset=["date"])

        # Fill stock split values
        if "stock_split" in df.columns:
            df["stock_split"] = df["stock_split"].fillna("None")

        logger.info(f"Data cleaned. Remaining rows: {len(df)}")

        return df

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        logger.info("Transforming data...")

        numeric_cols = [
            "open","high","low","close","volume",
            "shares_outstanding_bn","market_cap_usd_bn",
            "quarterly_revenue_usd_bn","sma_20","sma_50",
            "sma_200","rsi_14"
        ]

        # Convert numeric columns safely
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # Sort time-series
        df = df.sort_values("date")

        logger.info("Generating features...")

        # Feature engineering
        df["daily_return"] = df["close"].pct_change()
        df["price_range"] = df["high"] - df["low"]

        return df

    def load_to_file(self, df: pd.DataFrame, output_path: str):
        logger.info("Saving processed data to file...")

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        df.to_csv(output_path, index=False)

        logger.info(f"Data saved to {output_path}")

    def load_to_db(self, df: pd.DataFrame):
        logger.info("Loading data into PostgreSQL...")

        df.to_sql(
            "nvidia_stock_data",
            con=engine,
            if_exists="replace",
            index=False,
            chunksize=1000,
            method="multi"
        )

        logger.info("Database load completed successfully.")


    def run_pipeline(self, output_path: str):

        logger.info("Starting ETL pipeline...")

        df = self.extract()

        df = self.clean_data(df)

        df = self.transform(df)

        self.load_to_file(df, output_path)

        self.load_to_db(df)

        logger.info("ETL pipeline completed successfully.")


if __name__ == "__main__":

    input_path = input_data
    output_path = output_data

    etl = ETL(input_path)

    etl.run_pipeline(str(output_path))
