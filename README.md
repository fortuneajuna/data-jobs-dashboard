# Data Jobs Intelligence Platform

An end-to-end analytics platform that ingests job posting data, runs analytical queries, visualizes insights through a multi-page dashboard, and predicts salaries using machine learning.

## Preview
<img width="1386" height="870" alt="image" src="https://github.com/user-attachments/assets/8aed9da7-9e70-4a7b-80f3-d04ecedaefaf" />
<img width="1826" height="937" alt="image" src="https://github.com/user-attachments/assets/6dbd50ec-9f2b-4adb-ac8c-fa18203d4577" />
<img width="1896" height="948" alt="image" src="https://github.com/user-attachments/assets/e3dc7a7a-c916-4bfa-b540-b68d8b0c5a3b" />
<img width="1351" height="710" alt="image" src="https://github.com/user-attachments/assets/6f2b4b8f-7541-4bb6-ba4d-75c2d4e00716" />


## Architecture

```
CSV ──→ ETL ──→ DuckDB ──→ SQL Analytics
  │                │              │
  │                │         Dashboard (Streamlit)
  │                │              │
  │                └── ML Models ─┘
  │                           │
  └── Salary Prediction ──────┘
```

## Tech Stack

| Layer | Tool |
|---|---|
| Ingestion | Python, Pandas |
| Storage | DuckDB (embedded columnar) |
| Analytics | SQL (window functions, CTEs) |
| Dashboard | Streamlit, Plotly, NetworkX, PyVis |
| ML | scikit-learn, XGBoost, mlxtend |
| Quality | pytest, ruff, mypy, black |

## Quick Start

```bash
cp .env.example .env
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Ingest data
PYTHONPATH=. python etl/pipeline.py --file /path/to/jobs.csv

# Launch dashboard
streamlit run dashboard/app.py     # → http://localhost:8501

# Run tests
pytest tests/ -v
```

## Project Structure

```
├── etl/              # ETL pipeline
│   ├── extract.py    # CSV loading + schema validation
│   ├── transform.py  # Cleaning, feature engineering, skills normalization
│   ├── load.py       # DuckDB inserts with transaction rollback
│   └── pipeline.py   # CLI orchestrator
├── sql/              # Database schema + analytics
│   ├── schema.sql    # DDL for jobs + skills tables
│   └── analytics_queries.sql
├── dashboard/        # Streamlit application
│   ├── app.py        # Entry point
│   ├── pages/        # 7 dashboard pages
│   │   ├── 01_executive_summary.py
│   │   ├── 02_salary_analytics.py
│   │   ├── 03_skills_intelligence.py
│   │   ├── 04_remote_work_insights.py
│   │   ├── 05_company_insights.py
│   │   ├── 06_career_pathfinder.py
│   │   └── 07_salary_predictor.py
│   ├── utils/db.py   # Cached DuckDB connection
│   └── assets/style.css
├── models/           # ML training + saved artifacts
│   ├── train_salary_model.py
│   ├── recommender.py
│   └── *.joblib      # (gitignored)
├── tests/            # pytest suite (30 tests)
│   ├── conftest.py
│   ├── test_extract.py
│   ├── test_transform.py
│   ├── test_load.py
│   ├── test_pipeline.py
│   └── test_sql.py
├── data/             # (gitignored)
│   ├── raw/
│   └── processed/
├── requirements.txt
├── Dockerfile
└── .env.example
```

## Dashboard Pages

| Page | Description |
|---|---|
| **Executive Summary** | 6 KPIs, hiring/salary trends, top roles |
| **Salary Analytics** | Distribution, boxplots, country/role filters |
| **Skills Intelligence** | Top skills bar, demand heatmap, co-occurrence network, salary premium |
| **Remote Work Insights** | Remote vs onsite comparison, trend, country ranking |
| **Company Insights** | Top hiring, highest paying, remote friendliness |
| **Career Pathfinder** | Select a role → salary, skills, companies, country map |
| **Salary Predictor** | Enter job details → predicted salary via trained model |

## SQL Analytics

Eight analytical queries using DuckDB, including:

- **Skill Salary Premium** — measures salary uplift per skill using CTEs
- **Role Rankings** — `RANK()` and `DENSE_RANK()` with ties
- **Salary Trends** — month-over-month change via `LAG()` / `LEAD()`

## Machine Learning

Three regression models trained on job features:

| Model | Target |
|---|---|
| Linear Regression | salary_year_avg |
| Random Forest | (n_estimators=100) |
| XGBoost | (n_estimators=100) |

The best performing model is persisted with its `StandardScaler` and feature columns. A career recommendation engine uses mlxtend's apriori for association rule mining on skill co-occurrence.

## Docker

```bash
docker build -t data-jobs-platform .
docker run -p 8501:8501 data-jobs-platform
```

## Quality

```bash
ruff check .          # lint
mypy .                # typecheck
pytest tests/ -v      # 30 tests
```

## Future Improvements

- Automated pipeline scheduling (Apache Airflow / Prefect)
- Cloud DuckDB (MotherDuck) for persistent storage
- CI/CD with GitHub Actions
- Additional ML features: location encoding, company embeddings, posting date seasonality
- Data drift monitoring with Great Expectations
- Interactive filtering with cross-filter across dashboard pages
- Real-time data feeds via API ingestion
