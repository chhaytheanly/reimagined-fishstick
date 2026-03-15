from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

input_data = ROOT / "database" / "nvidia_stock_data_1999_2026.csv"
output_data = ROOT / "database" / "cleaned_nvidia_stock_data_1999_2026.csv"

__all__ = ["input_data", "output_data"]