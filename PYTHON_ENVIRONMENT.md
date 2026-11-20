# Python Environment

The analysis pipeline and notebook use the dependencies listed in `requirements.txt`.
The project was validated in this workspace with Python 3.14.7.

## Windows setup

From the project root, create and activate a virtual environment, then install the
project dependencies:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

The source dataset must be downloaded separately from the official Kaggle competition
page and placed in `data/raw/`. See `DATA_SOURCE.md` for the required files and access
instructions.

Run the pipeline and tests with the environment active:

```powershell
python run_analysis.py
python -m pytest
```

The generated dashboard JSON is written to
`frontend/public/data/financial_plan.json`. Review the competition redistribution
rules before publishing dataset-derived output; see `DATA_SOURCE.md`.
