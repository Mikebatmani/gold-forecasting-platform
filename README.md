# Gold Forecasting Platform

An open, reproducible research project that tests whether macroeconomic and inflation data can help forecast the direction of gold (XAU/USD) over a 3-month horizon.

> **Research project. Not investment advice.** Results, including null results, are reported as they are.

## Goal

Build a working data pipeline, a benchmarked forecasting system, and a public demo. The goal is **not** to prove the model beats the market. A rigorous, honest result is the deliverable, whichever way it comes out.

## Design

| Choice | Setting |
|---|---|
| Data frequency | Daily |
| Forecast target | Whether gold is higher or lower 63 trading days (about 3 months) ahead |
| Decision frequency | One decision per quarter |
| Validation | Walk-forward testing with purged splits, so the model never sees the future |
| Success test | Beats an "always long" benchmark on risk-adjusted return, out-of-sample, counted in independent quarters |

Models are built as a ladder. Each rung is kept only if it beats the previous one out-of-sample:
benchmarks, then a regime filter, then logistic regression, then optional XGBoost and Fed-text analysis.

## Data and freshness

Macro series are published on a schedule, so every series carries its **release date**. A value only appears in the dataset on or after the day the public could first see it, and each row records how many days old the latest value is. This avoids lookahead bias.

Planned free sources: [FRED](https://fred.stlouisfed.org), BLS, Federal Reserve Board, U.S. Treasury.

## Project structure

```
src/         Data collection and modelling code
tests/       Automated data-integrity checks
data/raw/    Downloaded source data (not committed)
data/processed/  Cleaned tables
docs/        Methodology notes and the sprint log
notebooks/   Exploration
```

## Setup

1. Create a free API key at https://fred.stlouisfed.org/docs/api/api_key.html
2. Copy `.env.example` to `.env` and paste your key into it. **Never commit `.env`.**
3. Install dependencies and run the connection check:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python src/check_fred.py
```

## Status

Sprint 1 of 24: project set-up. See `docs/sprint-log.md`.
