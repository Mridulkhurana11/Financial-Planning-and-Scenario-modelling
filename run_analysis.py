from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.financial_planning import run_pipeline


def main() -> None:
    data_dir = ROOT / "data" / "raw"
    output = ROOT / "frontend" / "public" / "data" / "financial_plan.json"
    payload = run_pipeline(data_dir, output)
    print("\nFinancial planning dataset prepared successfully")
    print(f"Historical rows: {payload['metadata']['historical_rows']:,}")
    print(f"Stores: {payload['metadata']['stores']}")
    print(f"Departments: {payload['metadata']['departments']}")
    print(f"Historical period: {payload['metadata']['historical_start']} to {payload['metadata']['historical_end']}")
    print(f"Forecast horizon: {payload['metadata']['forecast_weeks']} weeks")
    print(f"Backtest WMAE: ${payload['metrics']['holiday_weighted_mae_usd']:,.2f}")
    print(f"Dashboard JSON: {output}")


if __name__ == "__main__":
    main()
