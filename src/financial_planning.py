"""Walmart weekly sales FP&A planning pipeline.

The source dataset contains weekly sales, not an approved company budget or cost ledger.
All plan values and contribution-margin / operating-expense assumptions are therefore
explicitly labelled as illustrative planning assumptions.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import math

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

DATA_FILES = {
    "train": "train.csv",
    "test": "test.csv",
    "features": "features.csv",
    "stores": "stores.csv",
}

CATEGORICAL_FEATURES = ["Store", "Dept", "Type"]
NUMERIC_FEATURES = [
    "Size", "IsHoliday", "Temperature", "Fuel_Price",
    "MarkDown1", "MarkDown2", "MarkDown3", "MarkDown4", "MarkDown5",
    "CPI", "Unemployment", "weekofyear", "month", "quarter",
    "year_index", "week_sin", "week_cos", "lag_1", "lag_4", "lag_13",
    "rolling_mean_4", "rolling_mean_13", "rolling_std_13", "history_count",
]
FEATURE_COLUMNS = CATEGORICAL_FEATURES + NUMERIC_FEATURES
TARGET = "Weekly_Sales"

SCENARIOS: dict[str, dict[str, Any]] = {
    "Base case": {
        "description": "Model baseline with measured planning assumptions.",
        "demand_growth_pct": 0.0,
        "price_mix_pct": 0.0,
        "contribution_margin_pct": 26.0,
        "operating_expense_pct": 12.0,
    },
    "Upside": {
        "description": "Stronger demand and improved price / mix realisation.",
        "demand_growth_pct": 4.0,
        "price_mix_pct": 1.0,
        "contribution_margin_pct": 27.5,
        "operating_expense_pct": 11.5,
    },
    "Conservative": {
        "description": "Softer demand and higher operating cost pressure.",
        "demand_growth_pct": -3.0,
        "price_mix_pct": -0.5,
        "contribution_margin_pct": 24.0,
        "operating_expense_pct": 13.0,
    },
}


class DataValidationError(ValueError):
    """Raised when source files are missing or do not match the expected schema."""


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required dataset file not found: {path}\nSee START_HERE.md.")
    return pd.read_csv(path, low_memory=False)


def load_inputs(data_dir: str | Path) -> dict[str, pd.DataFrame]:
    """Load the four official competition files from a local data directory."""
    root = Path(data_dir)
    return {name: _read_csv(root / filename) for name, filename in DATA_FILES.items()}


def _normalise_date(df: pd.DataFrame, name: str) -> pd.DataFrame:
    out = df.copy()
    if "Date" not in out.columns:
        raise DataValidationError(f"{name} is missing the Date column.")
    out["Date"] = pd.to_datetime(out["Date"], errors="coerce")
    out = out.dropna(subset=["Date"])
    return out


def prepare_store_features(features: pd.DataFrame, stores: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Clean store-week exogenous features and enforce one row per Store/Date."""
    f = _normalise_date(features, "features.csv")
    s = stores.copy()
    required_f = {"Store", "Date", "IsHoliday", "Temperature", "Fuel_Price", "CPI", "Unemployment"}
    missing = sorted(required_f - set(f.columns))
    if missing:
        raise DataValidationError(f"features.csv is missing columns: {missing}")
    if not {"Store", "Type", "Size"}.issubset(s.columns):
        raise DataValidationError("stores.csv must contain Store, Type and Size.")

    f["Store"] = pd.to_numeric(f["Store"], errors="coerce")
    s["Store"] = pd.to_numeric(s["Store"], errors="coerce")
    f = f.dropna(subset=["Store"])
    s = s.dropna(subset=["Store"])
    f["Store"] = f["Store"].astype(int)
    s["Store"] = s["Store"].astype(int)
    f = f.sort_values(["Store", "Date"]).reset_index(drop=True)

    markdown_cols = [c for c in [f"MarkDown{i}" for i in range(1, 6)] if c in f.columns]
    for col in markdown_cols:
        f[col] = pd.to_numeric(f[col], errors="coerce").fillna(0.0)
    macro_cols = [c for c in ["Temperature", "Fuel_Price", "CPI", "Unemployment"] if c in f.columns]
    for col in macro_cols:
        f[col] = pd.to_numeric(f[col], errors="coerce")
        f[col] = f.groupby("Store", sort=False)[col].ffill()
        f[col] = f[col].fillna(f[col].median())
        f[col] = f[col].fillna(0.0)

    f["IsHoliday"] = f["IsHoliday"].astype(str).str.strip().str.lower().map(
        {"true": 1, "false": 0, "1": 1, "0": 0}
    ).fillna(0).astype(int)

    # Preserve exactly one feature row for each store/week. Duplicate source rows
    # are collapsed instead of multiplying sales during downstream joins.
    duplicate_keys = int(f.duplicated(["Store", "Date"], keep=False).sum())
    agg: dict[str, Any] = {c: "mean" for c in macro_cols + markdown_cols}
    agg["IsHoliday"] = "max"
    f = f.groupby(["Store", "Date"], as_index=False).agg(agg)

    s = s[["Store", "Type", "Size"]].drop_duplicates("Store")
    s["Type"] = s["Type"].fillna("Unknown").astype(str)
    s["Size"] = pd.to_numeric(s["Size"], errors="coerce")
    s["Size"] = s["Size"].fillna(s["Size"].median()).fillna(0)
    f = f.merge(s, on="Store", how="left", validate="many_to_one")
    f["Type"] = f["Type"].fillna("Unknown").astype(str)
    f["Size"] = f["Size"].fillna(float(s["Size"].median() or 0))
    return f, {
        "feature_source_rows": int(len(features)),
        "feature_rows_after_dedup": int(len(f)),
        "duplicate_store_week_rows_collapsed": duplicate_keys,
        "stores_in_metadata": int(s["Store"].nunique()),
    }


def clean_sales_table(df: pd.DataFrame, table_name: str, require_target: bool) -> tuple[pd.DataFrame, dict[str, Any]]:
    out = _normalise_date(df, table_name)
    required = {"Store", "Dept", "Date", "IsHoliday"}
    if require_target:
        required.add(TARGET)
    missing = sorted(required - set(out.columns))
    if missing:
        raise DataValidationError(f"{table_name} is missing columns: {missing}")

    for col in ["Store", "Dept"]:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    out = out.dropna(subset=["Store", "Dept"])
    out["Store"] = out["Store"].astype(int)
    out["Dept"] = out["Dept"].astype(int)
    out["IsHoliday"] = out["IsHoliday"].astype(str).str.strip().str.lower().map(
        {"true": 1, "false": 0, "1": 1, "0": 0}
    ).fillna(0).astype(int)

    removed_duplicates = int(out.duplicated(["Store", "Dept", "Date"]).sum())
    out = out.drop_duplicates(["Store", "Dept", "Date"], keep="last").copy()
    invalid_sales = 0
    if require_target:
        out[TARGET] = pd.to_numeric(out[TARGET], errors="coerce")
        invalid_sales = int(out[TARGET].isna().sum())
        out = out.dropna(subset=[TARGET]).copy()
        # Retain negative historical adjustments in actuals; forecasts are clipped at zero.
    return out.sort_values(["Date", "Store", "Dept"]).reset_index(drop=True), {
        "source_rows": int(len(df)),
        "usable_rows": int(len(out)),
        "duplicate_store_dept_week_rows_removed": removed_duplicates,
        "invalid_sales_rows_removed": invalid_sales,
    }


def merge_sales_features(sales: pd.DataFrame, feature_table: pd.DataFrame, name: str) -> tuple[pd.DataFrame, dict[str, Any]]:
    merged = sales.merge(feature_table, on=["Store", "Date"], how="left", suffixes=("", "_feature"), validate="many_to_one", indicator=True)
    unmatched = int((merged["_merge"] != "both").sum())
    merged = merged.drop(columns="_merge")
    if "IsHoliday_feature" in merged.columns:
        merged = merged.drop(columns="IsHoliday_feature")
    # Fill exogenous values after the merge; missing markdowns mean no recorded markdown.
    for col in [f"MarkDown{i}" for i in range(1, 6)]:
        if col not in merged.columns:
            merged[col] = 0.0
        merged[col] = pd.to_numeric(merged[col], errors="coerce").fillna(0.0)
    for col in ["Temperature", "Fuel_Price", "CPI", "Unemployment", "Size"]:
        if col not in merged.columns:
            merged[col] = np.nan
        merged[col] = pd.to_numeric(merged[col], errors="coerce")
        merged[col] = merged.groupby("Store", sort=False)[col].ffill()
        merged[col] = merged[col].fillna(merged[col].median()).fillna(0.0)
    if "Type" not in merged.columns:
        merged["Type"] = "Unknown"
    merged["Type"] = merged["Type"].fillna("Unknown").astype(str)
    return merged.drop(columns=[c for c in merged.columns if c.endswith("_feature")]), {
        f"{name.lower()}_rows_without_store_week_features": unmatched,
    }


def load_and_prepare(data_dir: str | Path) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Load, clean and join train/test sales to features and store metadata."""
    raw = load_inputs(data_dir)
    feature_table, feature_audit = prepare_store_features(raw["features"], raw["stores"])
    train, train_audit = clean_sales_table(raw["train"], "train.csv", require_target=True)
    test, test_audit = clean_sales_table(raw["test"], "test.csv", require_target=False)
    train_m, train_merge_audit = merge_sales_features(train, feature_table, "Train")
    test_m, test_merge_audit = merge_sales_features(test, feature_table, "Test")
    audit = {
        "source": "Walmart Recruiting - Store Sales Forecasting",
        "source_rows": {k: int(len(v)) for k, v in raw.items()},
        "train_cleaning": train_audit,
        "test_cleaning": test_audit,
        "feature_cleaning": feature_audit,
        **train_merge_audit,
        **test_merge_audit,
        "date_start": train_m["Date"].min().strftime("%Y-%m-%d"),
        "date_end": train_m["Date"].max().strftime("%Y-%m-%d"),
        "stores": int(train_m["Store"].nunique()),
        "departments": int(train_m["Dept"].nunique()),
        "store_types": sorted(train_m["Type"].unique().tolist()),
        "weeks": int(train_m["Date"].nunique()),
    }
    if train_m.empty or test_m.empty:
        raise DataValidationError("Training and test data must both contain usable rows.")
    return train_m, test_m, audit


def _add_calendar_features(df: pd.DataFrame, origin: pd.Timestamp) -> pd.DataFrame:
    out = df.copy()
    iso_week = out["Date"].dt.isocalendar().week.astype(int)
    out["weekofyear"] = iso_week.astype(float)
    out["month"] = out["Date"].dt.month.astype(float)
    out["quarter"] = out["Date"].dt.quarter.astype(float)
    out["year_index"] = (out["Date"] - origin).dt.days.astype(float) / 365.25
    out["week_sin"] = np.sin(2 * np.pi * iso_week / 52.18)
    out["week_cos"] = np.cos(2 * np.pi * iso_week / 52.18)
    return out


def make_training_features(train: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series, pd.DataFrame]:
    """Create strictly backward-looking lags and rolling features for training rows."""
    df = train.sort_values(["Store", "Dept", "Date"]).reset_index(drop=True).copy()
    origin = df["Date"].min()
    df = _add_calendar_features(df, origin)
    grouped = df.groupby(["Store", "Dept"], sort=False)[TARGET]
    df["history_count"] = df.groupby(["Store", "Dept"], sort=False).cumcount().astype(float)
    for lag in [1, 4, 13]:
        df[f"lag_{lag}"] = grouped.shift(lag)
    df["rolling_mean_4"] = grouped.transform(lambda s: s.shift(1).rolling(4, min_periods=1).mean())
    df["rolling_mean_13"] = grouped.transform(lambda s: s.shift(1).rolling(13, min_periods=1).mean())
    df["rolling_std_13"] = grouped.transform(lambda s: s.shift(1).rolling(13, min_periods=2).std())
    x = df[FEATURE_COLUMNS].copy()
    for col in CATEGORICAL_FEATURES:
        x[col] = x[col].astype("category")
    x[NUMERIC_FEATURES] = x[NUMERIC_FEATURES].replace([np.inf, -np.inf], np.nan)
    # Keep early observations; the model sees history_count and missing-lag indicators via fills.
    for col in NUMERIC_FEATURES:
        median = x[col].median()
        x[col] = x[col].fillna(float(median) if pd.notna(median) else 0.0)
    y = df[TARGET].astype(float)
    return x, y, df


def _build_model() -> HistGradientBoostingRegressor:
    return HistGradientBoostingRegressor(
        loss="squared_error",
        learning_rate=0.075,
        max_iter=130,
        max_leaf_nodes=31,
        min_samples_leaf=35,
        l2_regularization=2.0,
        categorical_features="from_dtype",
        early_stopping=True,
        validation_fraction=0.12,
        n_iter_no_change=12,
        random_state=42,
    )


def _category_maps(train: pd.DataFrame, future: pd.DataFrame) -> dict[str, list[Any]]:
    combined = pd.concat([train[CATEGORICAL_FEATURES], future[CATEGORICAL_FEATURES]], ignore_index=True)
    return {c: sorted(combined[c].dropna().unique().tolist()) for c in CATEGORICAL_FEATURES}


def _cast_features(x: pd.DataFrame, category_maps: dict[str, list[Any]]) -> pd.DataFrame:
    out = x[FEATURE_COLUMNS].copy()
    for col in CATEGORICAL_FEATURES:
        out[col] = pd.Categorical(out[col], categories=category_maps[col])
    for col in NUMERIC_FEATURES:
        out[col] = pd.to_numeric(out[col], errors="coerce").replace([np.inf, -np.inf], np.nan).fillna(0.0).astype(float)
    return out


def _make_history(history_df: pd.DataFrame) -> dict[tuple[int, int], list[float]]:
    history: dict[tuple[int, int], list[float]] = {}
    for (store, dept), group in history_df.sort_values("Date").groupby(["Store", "Dept"]):
        history[(int(store), int(dept))] = group[TARGET].astype(float).tolist()
    return history


def _future_feature_rows(batch: pd.DataFrame, history: dict[tuple[int, int], list[float]], origin: pd.Timestamp) -> pd.DataFrame:
    rows = _add_calendar_features(batch, origin)
    lag_values = {"lag_1": [], "lag_4": [], "lag_13": [], "rolling_mean_4": [], "rolling_mean_13": [], "rolling_std_13": [], "history_count": []}
    for r in rows.itertuples(index=False):
        vals = history.get((int(r.Store), int(r.Dept)), [])
        lag_values["lag_1"].append(vals[-1] if len(vals) >= 1 else np.nan)
        lag_values["lag_4"].append(vals[-4] if len(vals) >= 4 else np.nan)
        lag_values["lag_13"].append(vals[-13] if len(vals) >= 13 else np.nan)
        lag_values["rolling_mean_4"].append(float(np.mean(vals[-4:])) if vals else np.nan)
        lag_values["rolling_mean_13"].append(float(np.mean(vals[-13:])) if vals else np.nan)
        lag_values["rolling_std_13"].append(float(np.std(vals[-13:], ddof=1)) if len(vals) >= 2 else np.nan)
        lag_values["history_count"].append(float(len(vals)))
    for col, values in lag_values.items():
        rows[col] = values
    return rows[FEATURE_COLUMNS].copy()


def recursive_forecast(
    model: HistGradientBoostingRegressor,
    future_rows: pd.DataFrame,
    history_df: pd.DataFrame,
    category_maps: dict[str, list[Any]],
    origin: pd.Timestamp,
) -> pd.DataFrame:
    """Forecast a future schedule recursively so lags never use future actuals."""
    history = _make_history(history_df)
    forecast_parts = []
    future = future_rows.sort_values(["Date", "Store", "Dept"]).copy()
    for date, batch in future.groupby("Date", sort=True):
        features = _future_feature_rows(batch, history, origin)
        x = _cast_features(features, category_maps)
        predictions = np.maximum(model.predict(x), 0.0)
        part = batch[["Store", "Dept", "Date", "IsHoliday", "Type", "Size"]].copy()
        part["forecast_sales"] = predictions
        forecast_parts.append(part)
        for store, dept, prediction in zip(part["Store"], part["Dept"], predictions):
            history.setdefault((int(store), int(dept)), []).append(float(prediction))
    return pd.concat(forecast_parts, ignore_index=True) if forecast_parts else pd.DataFrame()


def _fit_and_backtest(train: pd.DataFrame, future: pd.DataFrame) -> tuple[HistGradientBoostingRegressor, dict[str, Any], dict[str, Any]]:
    x, y, features = make_training_features(train)
    categories = _category_maps(train, future)
    x = _cast_features(x, categories)
    unique_dates = sorted(train["Date"].drop_duplicates().tolist())
    validation_weeks = min(13, max(4, len(unique_dates) // 8))
    val_start = unique_dates[-validation_weeks]
    fit_mask = features["Date"] < val_start
    model_val = _build_model()
    model_val.fit(x.loc[fit_mask], y.loc[fit_mask])
    validation_rows = train.loc[train["Date"] >= val_start].copy()
    val_forecast = recursive_forecast(model_val, validation_rows, train.loc[train["Date"] < val_start], categories, train["Date"].min())
    compare = validation_rows[["Store", "Dept", "Date", "IsHoliday", TARGET]].merge(
        val_forecast[["Store", "Dept", "Date", "forecast_sales"]],
        on=["Store", "Dept", "Date"], how="inner", validate="one_to_one"
    )
    err = compare[TARGET] - compare["forecast_sales"]
    weights = np.where(compare["IsHoliday"].astype(int).to_numpy() == 1, 5.0, 1.0)
    wmae = float(np.average(np.abs(err), weights=weights))
    mae = float(mean_absolute_error(compare[TARGET], compare["forecast_sales"]))
    rmse = float(math.sqrt(mean_squared_error(compare[TARGET], compare["forecast_sales"])))
    weekly = compare.groupby("Date", as_index=False).agg(actual=(TARGET, "sum"), predicted=("forecast_sales", "sum"))
    weekly["absolute_pct_error"] = (weekly["actual"] - weekly["predicted"]).abs() / weekly["actual"].abs().clip(lower=1.0)
    band_pct = float(np.clip(weekly["absolute_pct_error"].quantile(0.90), 0.05, 0.35))
    weighted_den = float(np.sum(weights * np.abs(compare[TARGET].to_numpy())))
    wmape = float(np.sum(weights * np.abs(err.to_numpy())) / max(weighted_den, 1.0))
    weekly_records = _json_records(weekly, ["Date"])
    metrics = {
        "validation_weekly": weekly_records,
        "validation_start": pd.Timestamp(val_start).strftime("%Y-%m-%d"),
        "validation_weeks": int(validation_weeks),
        "validation_rows": int(len(compare)),
        "mae_usd": mae,
        "rmse_usd": rmse,
        "holiday_weighted_mae_usd": wmae,
        "holiday_weighted_mape": wmape,
        "backtest_p90_error_band_pct": band_pct,
        "evaluation_note": "Last 13 (or available minimum) weeks held out; recursive predictions use only prior actuals/predictions. Holiday rows receive 5x weight for weighted MAE.",
    }

    # Fit final model on all historical training rows.
    final_model = _build_model()
    final_model.fit(x, y)
    return final_model, metrics, {"category_maps": categories, "origin": train["Date"].min()}


def _build_reference_plan(train: pd.DataFrame, future_rows: pd.DataFrame) -> pd.Series:
    """Illustrative reference plan: same ISO week seasonal average × 1.02.

    This is not an approved Walmart budget. Fallback is the trailing 13-observation
    store/department mean where a seasonal cell is unavailable.
    """
    hist = train.copy()
    hist["iso_week"] = hist["Date"].dt.isocalendar().week.astype(int)
    seasonal = hist.groupby(["Store", "Dept", "iso_week"])[TARGET].mean().to_dict()
    trailing = hist.sort_values("Date").groupby(["Store", "Dept"])[TARGET].apply(lambda x: float(x.tail(13).mean())).to_dict()
    values = []
    for row in future_rows.itertuples(index=False):
        week = int(pd.Timestamp(row.Date).isocalendar().week)
        v = seasonal.get((int(row.Store), int(row.Dept), week))
        if v is None or not np.isfinite(v):
            v = trailing.get((int(row.Store), int(row.Dept)), float(hist[TARGET].median()))
        values.append(max(0.0, float(v) * 1.02))
    return pd.Series(values, index=future_rows.index, dtype=float)


def apply_scenario(forecast_sales: pd.Series | np.ndarray, assumptions: dict[str, float]) -> dict[str, np.ndarray]:
    """Apply transparent planning assumptions to the statistical revenue forecast."""
    raw = np.asarray(forecast_sales, dtype=float)
    demand = float(assumptions.get("demand_growth_pct", 0.0)) / 100.0
    price_mix = float(assumptions.get("price_mix_pct", 0.0)) / 100.0
    margin = float(assumptions.get("contribution_margin_pct", 26.0)) / 100.0
    opex = float(assumptions.get("operating_expense_pct", 12.0)) / 100.0
    revenue = np.maximum(raw * (1 + demand) * (1 + price_mix), 0.0)
    modelled_contribution = revenue * (margin - opex)
    return {"revenue": revenue, "modelled_gross_contribution": revenue * margin,
            "modelled_operating_expenses": revenue * opex,
            "modelled_operating_contribution": modelled_contribution}


def _json_records(df: pd.DataFrame, date_cols: list[str] | None = None) -> list[dict[str, Any]]:
    out = df.copy()
    for col in date_cols or []:
        if col in out.columns:
            out[col] = pd.to_datetime(out[col]).dt.strftime("%Y-%m-%d")
    out = out.replace({np.nan: None, np.inf: None, -np.inf: None})
    return json.loads(out.to_json(orient="records", date_format="iso"))


def build_dashboard_payload(
    train: pd.DataFrame,
    forecast: pd.DataFrame,
    metrics: dict[str, Any],
    audit: dict[str, Any],
    output_path: str | Path,
) -> dict[str, Any]:
    """Aggregate model outputs into the static JSON consumed by the Vite dashboard."""
    history_weekly = train.groupby("Date", as_index=False).agg(
        actual_sales=(TARGET, "sum"), holiday_week=("IsHoliday", "max"),
        store_count=("Store", "nunique"), department_count=("Dept", "nunique")
    ).sort_values("Date")
    forecast = forecast.copy()
    forecast["reference_plan"] = _build_reference_plan(train, forecast)
    band = float(metrics.get("backtest_p90_error_band_pct", 0.15))
    forecast_weekly = forecast.groupby("Date", as_index=False).agg(
        model_forecast=("forecast_sales", "sum"), reference_plan=("reference_plan", "sum"),
        holiday_week=("IsHoliday", "max"), store_count=("Store", "nunique")
    ).sort_values("Date")
    forecast_weekly["range_lower"] = forecast_weekly["model_forecast"] * (1 - band)
    forecast_weekly["range_upper"] = forecast_weekly["model_forecast"] * (1 + band)

    # 13-week blocks are labelled Q1/Q2/Q3 of the available forecast horizon.
    dates = sorted(forecast["Date"].drop_duplicates().tolist())
    q_map = {pd.Timestamp(d): f"Q{idx // 13 + 1}" for idx, d in enumerate(dates)}
    forecast["planning_quarter"] = forecast["Date"].map(q_map)
    segment_quarter = forecast.groupby(["Type", "planning_quarter"], as_index=False).agg(
        forecast_revenue=("forecast_sales", "sum"), reference_plan=("reference_plan", "sum"),
        stores=("Store", "nunique"), departments=("Dept", "nunique")
    )
    segment_quarter["variance"] = segment_quarter["forecast_revenue"] - segment_quarter["reference_plan"]
    segment_total = forecast.groupby("Type", as_index=False).agg(
        forecast_revenue=("forecast_sales", "sum"), reference_plan=("reference_plan", "sum"),
        stores=("Store", "nunique"), departments=("Dept", "nunique")
    )
    segment_total["variance"] = segment_total["forecast_revenue"] - segment_total["reference_plan"]

    historical_segment = train.sort_values("Date").groupby("Type", as_index=False).tail(1) if False else train.copy()
    last_13_dates = sorted(train["Date"].drop_duplicates().tolist())[-13:]
    recent = train[train["Date"].isin(last_13_dates)]
    recent_segment = recent.groupby("Type", as_index=False).agg(recent_actual=(TARGET, "sum"))

    store_actual = train.groupby(["Store", "Type"], as_index=False).agg(
        historical_sales=(TARGET, "sum"), departments=("Dept", "nunique")
    )
    store_recent = recent.groupby("Store", as_index=False).agg(recent_actual=(TARGET, "sum"))
    store_forecast = forecast.groupby(["Store", "Type"], as_index=False).agg(
        forecast_revenue=("forecast_sales", "sum"), reference_plan=("reference_plan", "sum")
    )
    store_performance = store_actual.merge(store_recent, on="Store", how="left").merge(
        store_forecast, on=["Store", "Type"], how="outer"
    )
    store_performance["variance"] = (
        store_performance["forecast_revenue"] - store_performance["reference_plan"]
    )

    department_actual = train.groupby("Dept", as_index=False).agg(
        historical_sales=(TARGET, "sum"), stores=("Store", "nunique")
    )
    department_recent = recent.groupby("Dept", as_index=False).agg(recent_actual=(TARGET, "sum"))
    department_forecast = forecast.groupby("Dept", as_index=False).agg(
        forecast_revenue=("forecast_sales", "sum"),
        reference_plan=("reference_plan", "sum"),
        forecast_stores=("Store", "nunique"),
    )
    department_performance = department_actual.merge(
        department_recent, on="Dept", how="outer"
    ).merge(department_forecast, on="Dept", how="outer")
    department_performance["variance"] = (
        department_performance["forecast_revenue"] - department_performance["reference_plan"]
    )

    holiday = train.groupby("IsHoliday")[TARGET].agg(["mean", "median", "count"]).reset_index()
    holiday_effect = {"holiday_average_weekly_sales": 0.0, "nonholiday_average_weekly_sales": 0.0, "holiday_lift_pct": 0.0}
    if len(holiday):
        h = float(holiday.loc[holiday["IsHoliday"] == 1, "mean"].iloc[0]) if (holiday["IsHoliday"] == 1).any() else 0.0
        nh = float(holiday.loc[holiday["IsHoliday"] == 0, "mean"].iloc[0]) if (holiday["IsHoliday"] == 0).any() else 0.0
        holiday_effect = {"holiday_average_weekly_sales": h, "nonholiday_average_weekly_sales": nh,
                          "holiday_lift_pct": (h / nh - 1) if nh else 0.0}

    monthly = train.assign(month=train["Date"].dt.to_period("M").dt.to_timestamp()).groupby("month", as_index=False).agg(
        actual_sales=(TARGET, "sum"), holiday_sales=(TARGET, lambda x: float(x[train.loc[x.index, "IsHoliday"] == 1].sum()))
    ).sort_values("month")
    month_records = _json_records(monthly, ["month"])

    # Historical series is capped to the last 52 weeks to keep the executive chart readable.
    history_records = _json_records(history_weekly.tail(52), ["Date"])
    forecast_records = _json_records(forecast_weekly, ["Date"])
    for row in segment_quarter.to_dict(orient="records"):
        for key, value in list(row.items()):
            if isinstance(value, (np.integer, np.floating)):
                row[key] = float(value) if np.isfinite(value) else None

    actual_52 = float(history_weekly.tail(52)["actual_sales"].sum())
    forecast_total = float(forecast_weekly["model_forecast"].sum())
    plan_total = float(forecast_weekly["reference_plan"].sum())
    contribution_base = apply_scenario(forecast_weekly["model_forecast"], SCENARIOS["Base case"])
    meta = {
        "dataset": "Walmart Recruiting - Store Sales Forecasting",
        "source_url": "https://www.kaggle.com/competitions/walmart-recruiting-store-sales-forecasting/data",
        "currency": "USD",
        "historical_start": train["Date"].min().strftime("%Y-%m-%d"),
        "historical_end": train["Date"].max().strftime("%Y-%m-%d"),
        "forecast_start": forecast_weekly["Date"].min().strftime("%Y-%m-%d"),
        "forecast_end": forecast_weekly["Date"].max().strftime("%Y-%m-%d"),
        "historical_rows": int(len(train)),
        "forecast_rows": int(len(forecast)),
        "stores": int(train["Store"].nunique()),
        "departments": int(train["Dept"].nunique()),
        "store_types": sorted(train["Type"].astype(str).unique().tolist()),
        "historical_weeks": int(train["Date"].nunique()),
        "forecast_weeks": int(forecast_weekly["Date"].nunique()),
        "plan_definition": "Illustrative reference plan: same ISO week historical average by store/department, with a 2% planning uplift. It is not an approved company budget.",
        "financial_assumption_note": "The source has Weekly_Sales but no COGS, payroll or operating expense ledger. Contribution and operating contribution are modelled using editable assumptions, not reported actual profit.",
        "forecast_band_note": "Indicative range derived from the 90th percentile of absolute weekly percentage errors in a recursive time-based backtest. It is not a calibrated probabilistic confidence interval.",
    }
    kpis = {
        "last_52_week_sales": actual_52,
        "forecast_revenue_base": forecast_total,
        "reference_plan_revenue": plan_total,
        "plan_variance": forecast_total - plan_total,
        "plan_variance_pct": (forecast_total / plan_total - 1) if plan_total else 0.0,
        "modelled_operating_contribution_base": float(np.sum(contribution_base["modelled_operating_contribution"])),
        "forecast_band_pct": band,
        "forecast_lower_base": forecast_total * (1 - band),
        "forecast_upper_base": forecast_total * (1 + band),
    }
    payload = {
        "metadata": meta,
        "kpis": kpis,
        "metrics": metrics,
        "audit": audit,
        "historical_weekly": history_records,
        "monthly_actuals": month_records,
        "forecast_weekly": forecast_records,
        "segments": _json_records(segment_total),
        "segment_quarter": _json_records(segment_quarter),
        "recent_segment_actuals": _json_records(recent_segment),
        "store_performance": _json_records(store_performance),
        "department_performance": _json_records(department_performance),
        "holiday_effect": holiday_effect,
        "scenario_presets": SCENARIOS,
        "methodology": {
            "model": "HistGradientBoostingRegressor with store/department/store-type categoricals, calendar, holiday, markdown, regional and lagged sales features.",
            "backtesting": metrics["evaluation_note"],
            "reference_plan": meta["plan_definition"],
        },
    }
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, allow_nan=False), encoding="utf-8")
    return payload


def run_pipeline(data_dir: str | Path, output_path: str | Path) -> dict[str, Any]:
    train, future, audit = load_and_prepare(data_dir)
    model, metrics, context = _fit_and_backtest(train, future)
    forecast = recursive_forecast(model, future, train, context["category_maps"], context["origin"])
    # Preserve external driver values for analytical review and forecasting context.
    forecast = forecast.merge(future[["Store", "Dept", "Date", "Temperature", "Fuel_Price", "CPI", "Unemployment", "IsHoliday"]],
                              on=["Store", "Dept", "Date", "IsHoliday"], how="left", validate="one_to_one")
    return build_dashboard_payload(train, forecast, metrics, audit, output_path)
