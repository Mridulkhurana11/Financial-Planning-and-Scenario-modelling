# Start Here — Northstar FP&A

## Fastest way to run it (Windows)

Double-click **`run_windows.bat`** in this folder. It does everything below automatically:
creates the Python environment, installs Python **and** frontend dependencies, regenerates the
dashboard data, and opens the dashboard at `http://localhost:5173`.

Keep the terminal window open while using the dashboard — closing it stops the server.
To restart only the dashboard later, double-click **`start_frontend.bat`**.

## Manual steps

### 1. Download data

From the [Walmart Recruiting Store Sales Forecasting Kaggle competition](https://www.kaggle.com/competitions/walmart-recruiting-store-sales-forecasting/data), download and extract:

- `train.csv`
- `test.csv`
- `features.csv`
- `stores.csv`

Place all four files in `data/raw/`. The source files are not bundled with this project; access is subject to Kaggle competition rules.

### 2. Create environment and run the analysis

Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run_analysis.py
```

The pipeline trains and backtests the model, forecasts the supplied test schedule, and generates `frontend/public/data/financial_plan.json`.

### 3. Explore in Jupyter

```powershell
pip install jupyterlab
jupyter lab
```

Open `notebooks/01_walmart_financial_planning_scenario_modelling.ipynb` and run from top to bottom.

### 4. Start the Vite dashboard

```powershell
cd frontend
npm install
npm run dev
```

`npm install` is required once on a fresh download; without it `npm run dev` reports
`'vite' is not recognized as an internal or external command`.

Also note that `python run_analysis.py` must be run with the virtual environment activated
(`.\.venv\Scripts\Activate.ps1`), otherwise the system Python reports
`ModuleNotFoundError: No module named 'pandas'`.

## 5. Deploy

After generating and reviewing the JSON, deploy the `frontend` directory to Vercel:

- Framework: Vite
- Root Directory: `frontend`
- Build Command: `npm run build`
- Output Directory: `dist`

Review Kaggle rules before publishing the generated data JSON publicly.
