# Jupyter Notebook Guide

Notebook: `notebooks/01_walmart_financial_planning_scenario_modelling.ipynb`

The notebook is designed to run from top to bottom and calls the same functions used by `run_analysis.py`.

Sections:
1. Environment and imports.
2. Load source tables.
3. Prepare and validate analytical tables.
4. Historical weekly sales performance.
5. Store format and department mix.
6. Holiday and external-driver analysis.
7. Backward-looking feature engineering.
8. Time-based recursive backtest.
9. Forecast competition test horizon.
10. Scenario modelling.
11. Generate dashboard JSON.
12. Interpretation and limitations.

Run from the repository root with the Python virtual environment activated:

```powershell
pip install -r requirements.txt
pip install jupyterlab
jupyter lab
```

The notebook requires the four CSV files in `data/raw/`.
