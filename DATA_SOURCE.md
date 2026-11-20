# Data Source & Access Notes

## Walmart Recruiting — Store Sales Forecasting

Official Kaggle competition data page:
https://www.kaggle.com/competitions/walmart-recruiting-store-sales-forecasting/data

The competition describes weekly department sales for 45 Walmart stores, along with store metadata and store-week external features. The historical training data spans approximately February 2010 to November 2012. The commonly used original training release contains approximately 421,570 rows; the pipeline prints the exact number of rows in the copy you download.

## Required files

| File | Key fields | Use |
|---|---|---|
| `train.csv` | Store, Dept, Date, Weekly_Sales, IsHoliday | Historical target and holiday flag |
| `test.csv` | Store, Dept, Date, IsHoliday | Future prediction schedule |
| `features.csv` | Store, Date, Temperature, Fuel_Price, MarkDown1–5, CPI, Unemployment, IsHoliday | Regional / promotional context |
| `stores.csv` | Store, Type, Size | Store format and size |

The source describes `MarkDown1` through `MarkDown5` as anonymised promotional markdown features. They are not guaranteed to be populated for every store-week.

## Download steps

1. Sign in to Kaggle.
2. Open the official competition data page above.
3. Accept the competition terms if prompted.
4. Download the files and extract them.
5. Place `train.csv`, `test.csv`, `features.csv` and `stores.csv` in this project's `data/raw/` directory.

## Licensing / redistribution caution

The [official competition rules](https://www.kaggle.com/competitions/walmart-recruiting-store-sales-forecasting/rules) bind data access to those rules. Reviewed on 2026-11-20, they did not provide an explicit general license for public redistribution of the source files. This project therefore does not bundle the source CSVs and excludes `data/raw/*.csv` from Git by default.

Do not publish raw files, test data, or dataset-derived results (including aggregate dashboard JSON) in a public repository or public website unless the current rules or a separate permission clearly allow that redistribution. Kaggle download access is not an unrestricted open-data licence. If redistribution is not authorized, obtain the source files separately using the steps above and regenerate derived outputs locally.

## Data interpretation

- `Weekly_Sales` is the source sales measure in US dollars.
- Store types A/B/C are anonymised store formats.
- `Dept` is an anonymised department identifier.
- The dataset is historical and should not be presented as a current Walmart forecast or official Walmart analysis.
- The source does not provide product-level COGS, payroll, operating expenses, approved budgets or cash flows.
