# AGENTS.md — data-jobs-platform

## Quick start

```bash
cp .env.example .env
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=. python etl/pipeline.py --file data/raw/jobs.csv
```

`etl/pipeline.py --file` defaults to `$RAW_DATA_PATH` (fallback `data/raw/jobs.csv`).

## Commands

| What | How |
|---|---|
| Run pipeline | `PYTHONPATH=. python etl/pipeline.py --file <path>` |
| Run dashboard | `streamlit run dashboard/app.py` (port 8501) |
| Run tests | `pytest` (or `pytest tests/ -v`) |
| Train salary model | `PYTHONPATH=. python models/train_salary_model.py` |
| Build recommender | `PYTHONPATH=. python models/recommender.py` |
| Format | `black .` |
| Lint | `ruff check .` |
| Typecheck | `mypy .` |
| Lint → typecheck → test | `ruff check . && mypy . && pytest` |

`pytest` works from repo root without `PYTHONPATH`; the pipeline/model scripts and dashboard need it (root locally, `/app` in Docker).

## Architecture

- **`etl/`** — pipeline: `extract.py` (CSV, 17-col schema) → `transform.py` (clean, feature-engineer, normalize skills) → `load.py` (DuckDB inserts) → `pipeline.py` (orchestrator with `--file` CLI)
- **`sql/`** — `schema.sql` DDL + `analytics_queries.sql` (8 queries: top roles, skill premium, rankings, trends)
- **`dashboard/`** — 7 Streamlit pages + salary predictor form. Pages read the DB via `dashboard/utils/db.py` (cached, path-safe); `app.py` → `pages/` (streamlit number prefixes)
- **`models/`** — `train_salary_model.py` (LR/RF/XGBoost), `recommender.py` (mlxtend apriori), saved `.joblib` artifacts (gitignored). `model_comparison.csv` is tracked.
- **`data/`** — `raw/` input, `processed/` output (both gitignored)
- **`lib/`** — vendored pyvis assets (vis-network, tom-select, bindings); generated, not project code — don't edit
- **`notebooks/`** — empty

## Database

- Local DuckDB at `data/processed/jobs.duckdb`. `MOTHERDUCK_TOKEN` is still honored by `etl/load.py` if set, but MotherDuck is not in `requirements.txt`.
- No star schema — flat `jobs` table + long `skills` table, no migration files. `load.py` does `DELETE FROM` then re-inserts (idempotent reload).

## Style & gotchas

- `tests/test_sql.py` **skips** (not fails) if `data/processed/jobs.duckdb` is missing — run the pipeline first or SQL query tests won't run. 30 tests total = 22 unit + 8 parametrized query blocks.
- `models/train_salary_model.py` and `models/recommender.py` resolve the DB via `Path.cwd()` — **must run from repo root**. The dashboard resolves paths relative to its files, so it works from any cwd.
- Dashboard `07_salary_predictor.py` requires trained `salary_model.joblib` / `scaler.joblib` / `feature_columns.joblib`; run `models/train_salary_model.py` first. Recommender artifacts (`association_rules.joblib`, `role_skills.joblib`) are trained but currently unused by the dashboard.
- `.env` gitignored; copy `.env.example`. Raw CSVs, DuckDB files, model binaries, notebook checkpoints all gitignored.
- No `pyproject.toml` / `setup.cfg` / `mypy.ini` — black, ruff, and mypy run on defaults.