# Analysis Methodology

## 1. Source tables and join grain

The model uses four competition files. `train.csv` and `test.csv` are at Store × Department × Week grain. `features.csv` is at Store × Week grain. `stores.csv` is at Store grain.

The pipeline collapses duplicate feature rows to one Store × Date record before joining. Store metadata is reduced to one row per Store. Joins are validated as many-to-one so a duplicated feature key cannot multiply weekly sales.

## 2. Cleaning

- Parse `Date` as a datetime.
- Convert Store and Dept to integer identifiers.
- Normalize `IsHoliday` to 0/1.
- Drop invalid keys and invalid training target values.
- Remove duplicate Store × Dept × Date records, retaining the last row.
- Retain negative weekly actuals because they can represent adjustments in the supplied history.
- Fill missing markdown fields with zero, reflecting no recorded markdown amount in the source row.
- Forward-fill temperature, fuel price, CPI and unemployment within Store; use a global median fallback if still missing.
- Preserve store type and size from `stores.csv`.

The audit in the generated dashboard JSON records rows, duplicate keys and feature-match gaps.

## 3. Features

Features include:

- Store, Department and store Type categorical identifiers.
- Store size.
- Holiday flag.
- Temperature, fuel price, CPI and unemployment.
- Markdown 1–5.
- ISO week of year, month, quarter, year index and cyclical week encodings.
- Lagged sales: 1, 4 and 13 observations.
- Rolling mean over the previous 4 and 13 observations.
- Rolling standard deviation over the previous 13 observations.
- Historical observation count.

All lag and rolling statistics are calculated using shifted history. The target for the current row is never used as a predictor.

## 4. Forecast model and validation

A pooled `HistGradientBoostingRegressor` is trained across Store × Department series. Store, Dept and Type are categorical features. Continuous features are numeric. The final 13 available historical weeks (or a shorter minimum for small fixtures) form the time-based holdout.

Validation is recursive. The first holdout week uses only pre-holdout actual history. Predictions from each future week are then appended to history and used to construct the next week's lag features. This avoids using holdout actual sales as future lags.

Metrics:

- MAE.
- RMSE.
- Holiday-weighted MAE (holiday rows receive weight 5).
- Holiday-weighted MAPE.
- P90 of weekly absolute percentage error, clipped to a 5%–35% envelope for the dashboard's indicative band.

The P90 band is an empirical historical error envelope from a single backtest, not a probabilistic confidence interval.

## 5. Reference plan

No approved plan/budget is included in the source. The model constructs an illustrative reference plan for each future Store × Department × ISO week:

`Reference Plan = Historical same-ISO-week average × 1.02`

If a seasonal cell is unavailable, it falls back to the trailing 13-observation average for that Store × Department, then multiplies by 1.02. This is a comparison baseline, not an actual Walmart budget.

## 6. Scenario model

The statistical model outputs baseline weekly sales. Scenario drivers then adjust the forecast:

`Scenario Revenue = Model Forecast × (1 + demand growth) × (1 + price/mix change)`

`Modelled Gross Contribution = Scenario Revenue × assumed contribution margin`

`Modelled Operating Expenses = Scenario Revenue × assumed operating expense rate`

`Modelled Operating Contribution = Modelled Gross Contribution − Modelled Operating Expenses`

The margin and operating expense assumptions are not learned from the source and are not actual financial statements. The interface makes these assumptions editable and labels the contribution values as modelled.

## 7. Planning periods and business lines

Forecast weeks are grouped into consecutive 13-week planning blocks (Q1, Q2, Q3, etc.). Store Type A/B/C is used as the available business-line proxy. Department identifiers remain anonymised.

## 8. Limitations

- Historical period is 2010–2012.
- Weekly sales are not a full accounting ledger.
- No actual budget, COGS, labour, opex, working capital or cash-flow series exists in the dataset.
- Markdown data is sparse.
- Store and department IDs are anonymised.
- Model quality is evaluated on one recursive time-based holdout; production work should use multiple rolling-origin backtests and business review.
