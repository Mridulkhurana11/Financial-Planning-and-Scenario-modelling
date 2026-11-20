# Northstar FP&A — Financial Planning & Scenario Modelling

An end-to-end financial planning portfolio project using the **Walmart Recruiting – Store Sales Forecasting** dataset. It combines a reproducible Python/Pandas forecasting pipeline, time-aware machine learning, a guided Jupyter notebook and a React + Vite planning dashboard.

**Python · Pandas · Scikit-learn · HistGradientBoosting · Time-series Backtesting · Scenario Modelling · React · Vite · Recharts · Vercel**

> Independent portfolio project using historical competition data. It is not affiliated with, commissioned by, or an official financial planning tool for Walmart.

## Project at a glance

The original Microsoft Financial Sample workbook was too small for a substantial forecasting exercise. This project uses a much larger panel of weekly sales observations across 45 stores and many departments. The commonly distributed original competition training file contains approximately 421,570 store-department-week observations; the exact row count is printed by the pipeline after download.

The application answers:

- What does the historical weekly sales trajectory look like?
- How do store formats contribute to the network's sales?
- How do holiday weeks and regional drivers relate to sales?
- What does a recursive, time-aware weekly sales forecast look like?
- How do transparent demand, price/mix and cost assumptions change the planning outcome?

## Why this dataset

The Walmart Recruiting competition dataset provides:

- `train.csv`: historical weekly sales by store and department.
- `test.csv`: future store / department / week combinations with the sales target withheld.
- `features.csv`: store-week context including temperature, fuel price, markdowns, CPI, unemployment and holiday flags.
- `stores.csv`: store format and store size.

This creates a more meaningful forecasting panel than a small, pre-aggregated financial sample. It includes multiple stores, departments, weekly seasonality, holiday indicators, promotional markdown fields and regional economic variables.

**Dataset source:** [Walmart Recruiting – Store Sales Forecasting (Kaggle)](https://www.kaggle.com/competitions/walmart-recruiting-store-sales-forecasting/data)

Access and use are subject to the Kaggle competition rules. The raw competition files are not bundled with this ZIP. Review the current competition rules before redistributing raw data or derived data publicly. See [DATA_SOURCE.md](DATA_SOURCE.md).

## Important financial interpretation

This dataset contains `Weekly_Sales`, not an approved corporate budget or a complete finance ledger. It does **not** contain actual COGS, payroll, operating expenses, EBITDA, working capital or cash-flow statements.

To make this a useful FP&A exercise without inventing historical financials:

1. Weekly sales are treated as the observed revenue measure.
2. A clearly labelled **illustrative reference plan** is calculated as the historical same-ISO-week average for each store / department, with a 2% planning uplift. It is not a management-approved budget.
3. The statistical model predicts weekly sales using only past sales and known week / store features.
4. Demand growth, price/mix, contribution margin and operating expense rates are explicit, editable planning assumptions.
5. “Modelled operating contribution” is calculated from forecast revenue and assumed rates. It is **not** reported profit, EBITDA or cash flow.
6. The forecast range is an indicative P90 error envelope from a recursive holdout backtest, not a calibrated probabilistic confidence interval.

These boundaries are part of the analytical story and should be explained in an interview.

## Repository structure

```text
walmart-financial-planning/
├── data/
│   └── raw/                         # Place train/test/features/stores CSVs here
├── notebooks/
│   └── 01_walmart_financial_planning_scenario_modelling.ipynb
├── src/
│   └── financial_planning.py        # Cleaning, features, backtest, forecast, scenario logic
├── tests/
│   └── test_financial_planning.py
├── outputs/                         # Local outputs (not required by frontend)
├── frontend/
│   ├── public/data/
│   │   └── financial_plan.json     # Generated data consumed by Vite
│   ├── src/
│   ├── package.json
│   └── vite.config.js
├── run_analysis.py
├── run_windows.bat
├── requirements.txt
├── ANALYSIS_METHODOLOGY.md
├── DATA_SOURCE.md
├── PORTFOLIO_CASE_STUDY.md
├── JUPYTER_GUIDE.md
└── START_HERE.md
```

## Get the data

1. Sign in to Kaggle and open the [competition data page](https://www.kaggle.com/competitions/walmart-recruiting-store-sales-forecasting/data).
2. Accept the competition rules if Kaggle requires it.
3. Download the competition data and extract the CSVs.
4. Copy these four files into `data/raw/`:
   - `train.csv`
   - `test.csv`
   - `features.csv`
   - `stores.csv`

The pipeline does not require `sampleSubmission.csv`.

## Run locally

### Quick start (Windows)

Double-click **`run_windows.bat`**. It creates the virtual environment, installs both Python and
frontend dependencies, regenerates the dashboard data and starts the dashboard at
`http://localhost:5173`. Keep the window open while using the app.

If you only need to restart the dashboard later, double-click **`start_frontend.bat`**.

### Manual setup

#### 1. Create a Python environment

Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

#### 2. Run the analysis and forecasting pipeline

From the repository root:

```bash
python run_analysis.py
```

The pipeline:

- validates the four source files;
- parses dates and numeric fields;
- removes duplicate store / department / week keys;
- collapses duplicate store-week feature rows before joins;
- fills sparse markdown values with zero and imputes regional fields transparently;
- creates backward-looking lag and rolling features;
- trains and time-backtests a HistGradientBoostingRegressor;
- forecasts the competition test schedule recursively;
- calculates the illustrative same-week reference plan;
- writes the aggregate JSON consumed by the dashboard.

Generated dashboard data:

```text
frontend/public/data/financial_plan.json
```

#### 3. Explore the Jupyter notebook

```bash
python -m pip install jupyterlab
jupyter lab
```

Open:

`notebooks/01_walmart_financial_planning_scenario_modelling.ipynb`

Run cells from top to bottom. The notebook uses the same functions as `run_analysis.py`, so it documents the application pipeline rather than a disconnected tutorial.

#### 4. Run the Vite dashboard

```bash
cd frontend
npm install
npm run dev
```

`npm install` is required once on a fresh download — `node_modules` is not included in the ZIP.
If it is skipped, `npm run dev` fails with `'vite' is not recognized as an internal or external command`.

Open the local URL printed by Vite, normally `http://localhost:5173`. The terminal running
`npm run dev` must stay open; closing it stops the dashboard.

The dashboard has no file-upload interface. It reads the fixed JSON generated by the Python pipeline.

> **Note:** `python run_analysis.py` only works with the virtual environment activated, because
> pandas/scikit-learn are installed in `.venv`, not in the system Python. Use
> `.\.venv\Scripts\python.exe run_analysis.py` if you have not activated it.

## Dashboard pages

- **Revenue forecast:** historical weekly actuals, reference plan, selected forecast, indicative backtest error band, forecast KPIs and store-format summary.
- **Scenario planning:** base, upside and conservative cases with editable demand, price/mix, contribution-margin and operating-expense assumptions.
- **Business lines:** store-type forecast comparison and 13-week planning blocks.
- **Model & data:** recursive backtest, WMAE / WMAPE / RMSE, dataset profile, cleaning audit and methodology notes.

## Vercel deployment

The frontend is a static React/Vite application. Python runs locally or in a controlled analysis environment; Vercel serves the prepared JSON and built frontend.

Before deployment:

1. Download the competition data locally.
2. Run `python run_analysis.py`.
3. Confirm `frontend/public/data/financial_plan.json` exists and is valid.
4. Review the Kaggle competition terms before making derived output publicly accessible.
5. Push the frontend and approved generated dashboard JSON to the repository.

Vercel settings:

| Setting | Value |
|---|---|
| Framework Preset | Vite |
| Root Directory | `frontend` |
| Build Command | `npm run build` |
| Output Directory | `dist` |
| Install Command | `npm install` |
| Node.js | 20 or later (22 recommended) |

## Tests

From the repository root:

```bash
python -m pytest
```

The unit tests cover duplicate-key handling, feature-table deduplication, backward-looking lag features and scenario calculations. The full competition data is needed for an end-to-end run.

## Limitations and responsible presentation

- Historical observations are from the 2010–2012 competition period; they are not current Walmart operating results.
- Store and department identifiers are anonymised; do not infer actual store locations or department names.
- The test-period forecast is an exercise in forecasting, not a verified prediction of actual future Walmart sales.
- Markdown features are sparse by design in parts of the history. Missing markdown values are set to zero; macro features are forward-filled within store and then median-imputed.
- Negative historical weekly sales are retained as source adjustments; forecast values are clipped at zero.
- The model is a portfolio demonstration. A production FP&A process would need finance-owned budgets, audited cost drivers, reconciliation, rolling-origin validation and forecast governance.

## Suggested portfolio description

**Northstar FP&A — Financial Planning & Scenario Modelling** is an end-to-end planning workspace built on a 421k-row weekly retail sales panel. It combines Pandas data preparation, time-aware machine-learning forecasts, recursive backtesting, transparent reference-plan construction and editable financial scenarios in a React/Vite dashboard, with a guided Jupyter notebook for reproducibility.
#   F i n a n c i a l - P l a n n i n g - a n d - S c e n a r i o - m o d e l l i n g  
 