import numpy as np
import pandas as pd

from src.financial_planning import (
    apply_scenario,
    build_dashboard_payload,
    clean_sales_table,
    make_training_features,
    prepare_store_features,
)


def test_clean_sales_keeps_negative_adjustments_and_removes_duplicate_key():
    df = pd.DataFrame({
        "Store": [1, 1, 1], "Dept": [2, 2, 2],
        "Date": ["2012-01-06", "2012-01-06", "2012-01-13"],
        "Weekly_Sales": [100.0, 100.0, -10.0],
        "IsHoliday": [False, False, False],
    })
    clean, audit = clean_sales_table(df, "train.csv", require_target=True)
    assert len(clean) == 2
    assert clean["Weekly_Sales"].min() == -10.0
    assert audit["duplicate_store_dept_week_rows_removed"] == 1


def test_prepare_store_features_collapses_duplicate_store_week():
    features = pd.DataFrame({
        "Store": [1, 1], "Date": ["2012-01-06", "2012-01-06"],
        "IsHoliday": [False, True], "Temperature": [10.0, 12.0],
        "Fuel_Price": [3.1, 3.2], "CPI": [210.0, 211.0], "Unemployment": [8.0, 8.1],
        "MarkDown1": [np.nan, 10.0],
    })
    stores = pd.DataFrame({"Store": [1], "Type": ["A"], "Size": [150000]})
    table, audit = prepare_store_features(features, stores)
    assert len(table) == 1
    assert table.loc[0, "IsHoliday"] == 1
    assert audit["duplicate_store_week_rows_collapsed"] == 2


def test_training_features_are_backward_looking():
    dates = pd.date_range("2011-01-07", periods=20, freq="W-FRI")
    df = pd.DataFrame({
        "Store": 1, "Dept": 1, "Date": dates, "Weekly_Sales": np.arange(100, 120, dtype=float),
        "IsHoliday": 0, "Type": "A", "Size": 100000,
        "Temperature": 20, "Fuel_Price": 3, "CPI": 210, "Unemployment": 8,
        **{f"MarkDown{i}": 0 for i in range(1, 6)},
    })
    x, y, enriched = make_training_features(df)
    assert enriched.loc[10, "lag_1"] == 109.0
    assert enriched.loc[10, "lag_4"] == 106.0
    assert enriched.loc[10, "lag_13"] == 97.0 if 10 >= 13 else pd.isna(enriched.loc[10, "lag_13"])
    assert len(x) == len(y) == len(df)


def test_scenario_model_is_transparent_and_nonnegative():
    base = np.array([100.0, 200.0])
    result = apply_scenario(base, {
        "demand_growth_pct": 10,
        "price_mix_pct": 5,
        "contribution_margin_pct": 30,
        "operating_expense_pct": 12,
    })
    assert np.allclose(result["revenue"], [115.5, 231.0])
    assert np.allclose(result["modelled_operating_contribution"], result["revenue"] * 0.18)
    assert (result["revenue"] >= 0).all()


def test_dashboard_payload_includes_store_and_department_performance(tmp_path):
    dates = pd.to_datetime(["2020-01-03", "2020-01-10"])
    train = pd.DataFrame({
        "Store": [1, 2], "Dept": [10, 20], "Type": ["A", "B"],
        "Date": dates, "Weekly_Sales": [100.0, 200.0], "IsHoliday": [0, 0],
    })
    forecast = pd.DataFrame({
        "Store": [1, 2], "Dept": [10, 20], "Type": ["A", "B"],
        "Date": pd.to_datetime(["2020-01-17", "2020-01-17"]),
        "forecast_sales": [120.0, 230.0], "IsHoliday": [0, 0],
    })
    payload = build_dashboard_payload(
        train,
        forecast,
        {"backtest_p90_error_band_pct": 0.1, "evaluation_note": "recursive holdout"},
        {},
        tmp_path / "financial_plan.json",
    )

    store_one = next(row for row in payload["store_performance"] if row["Store"] == 1)
    department_ten = next(row for row in payload["department_performance"] if row["Dept"] == 10)
    assert store_one["historical_sales"] == 100.0
    assert store_one["forecast_revenue"] == 120.0
    assert department_ten["historical_sales"] == 100.0
    assert department_ten["forecast_revenue"] == 120.0
