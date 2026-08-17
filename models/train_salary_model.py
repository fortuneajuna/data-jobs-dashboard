import logging
import os
from pathlib import Path

import duckdb
import joblib
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

MODELS_DIR = Path(__file__).resolve().parent


def load_data() -> pd.DataFrame:
    db_path = os.getenv("DUCKDB_PATH", "data/processed/jobs.duckdb")
    conn = duckdb.connect(str(Path.cwd() / db_path))

    df = conn.execute("""
        SELECT j.job_id, j.job_title_short, j.job_country, j.is_remote,
               j.requires_degree, j.offers_health_insurance, j.skill_count,
               j.salary_year_avg
        FROM jobs j
        WHERE j.salary_year_avg IS NOT NULL
    """).fetchdf()

    skills = conn.execute("""
        SELECT job_id, skill FROM skills
    """).fetchdf()

    conn.close()

    if df.empty:
        return df

    skill_dummies = skills.pivot_table(
        index="job_id", columns="skill", aggfunc="size", fill_value=0
    ).reset_index()

    df = df.merge(skill_dummies, on="job_id", how="left").fillna(0)
    return df


def train_model(df: pd.DataFrame):
    drop_cols = ["job_id", "salary_year_avg"]

    df = pd.get_dummies(df, columns=["job_title_short", "job_country"], drop_first=True)
    feature_cols = [c for c in df.columns if c not in drop_cols]

    X = df[feature_cols].values
    y = df["salary_year_avg"].values

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.2, random_state=42
    )

    models = {
        "LinearRegression": LinearRegression(),
        "RandomForest": RandomForestRegressor(n_estimators=100, random_state=42),
        "XGBoost": XGBRegressor(n_estimators=100, random_state=42, verbosity=0),
    }

    best_model = None
    best_score = -np.inf
    results = []

    for name, model in models.items():
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        r2 = r2_score(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        results.append({"model": name, "R2": r2, "MAE": mae, "RMSE": rmse})
        logger.info(f"{name}: R2={r2:.4f}, MAE={mae:.2f}, RMSE={rmse:.2f}")

        if not np.isnan(r2) and r2 > best_score:
            best_score = r2
            best_model = model

    results_df = pd.DataFrame(results).sort_values("R2", ascending=False)
    results_df.to_csv(MODELS_DIR / "model_comparison.csv", index=False)

    if best_model is None:
        logger.warning("No valid model found — using LinearRegression as fallback")
        best_model = LinearRegression()
        best_model.fit(X_train, y_train)
        joblib.dump(best_model, MODELS_DIR / "salary_model.joblib")
    else:
        joblib.dump(best_model, MODELS_DIR / "salary_model.joblib")
        logger.info(f"Best model: {best_model.__class__.__name__} (R2={best_score:.4f})")

    joblib.dump(scaler, MODELS_DIR / "scaler.joblib")
    joblib.dump(feature_cols, MODELS_DIR / "feature_columns.joblib")
    logger.info("Saved model artifacts")


def main():
    df = load_data()
    if df.empty:
        logger.warning("No salary data — skipping training")
        return
    logger.info(f"Loaded {len(df)} records with salary data")
    train_model(df)


if __name__ == "__main__":
    main()
