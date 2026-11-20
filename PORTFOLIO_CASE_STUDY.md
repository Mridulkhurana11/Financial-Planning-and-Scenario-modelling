# Portfolio Case Study — Northstar FP&A

## Business question

How can a multi-store retailer translate granular weekly sales history into a practical near-term financial planning view, compare a forecast with a transparent reference plan, and understand the impact of changing operating assumptions?

## Context

The project uses the historical Walmart Recruiting Store Sales Forecasting competition dataset, which contains store/department/week sales and contextual features. It is an independent analysis of historical sample data, not an official Walmart engagement.

## Approach

1. Validate source tables and preserve Store × Department × Week grain.
2. Join store-week context and store metadata without multiplying the sales records.
3. Build seasonal, holiday, macro, markdown and lagged sales features.
4. Train a pooled gradient-boosting model.
5. Evaluate it using a recursive time-based holdout and holiday-weighted error metrics.
6. Forecast the competition's future test schedule recursively.
7. Build a same-week historical reference plan with a clearly disclosed 2% planning uplift.
8. Add editable demand, price/mix, contribution-margin and opex assumptions.
9. Deliver the planning view in a Vite dashboard and document the logic in a Jupyter notebook.

## What the dashboard demonstrates

- Revenue forecast and reference-plan variance.
- Base, upside and conservative scenario comparison.
- Store-format planning view.
- Forecast model diagnostics and data quality.
- Explicit treatment of assumptions and model limitations.

## Important limitations

The source does not include actual COGS, payroll, approved budgets or cash flow. Scenario contribution values are illustrative model outputs, not reported profit, EBITDA or cash flow. The historical sample is from 2010–2012 and must not be represented as current Walmart performance.

## Interview discussion prompts

- Why was a recursive holdout selected instead of random train/test splitting?
- How did the pipeline avoid target leakage in lag features?
- Why are holiday observations weighted more heavily in WMAE?
- How is the reference plan different from a management-approved budget?
- What additional finance data would be needed for a true P&L forecast?
- How would rolling-origin validation and forecast governance improve the model?
