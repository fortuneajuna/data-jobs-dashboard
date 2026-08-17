from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import streamlit as st

from dashboard.utils.db import query
from dashboard.utils.theme import apply_theme

apply_theme()

st.title("Salary Predictor")

# Model loading

models_dir = Path(__file__).resolve().parent.parent.parent / "models"

model_path = models_dir / "salary_model.joblib"
scaler_path = models_dir / "scaler.joblib"
cols_path   = models_dir / "feature_columns.joblib"

models_ready = all(p.exists() for p in [model_path, scaler_path, cols_path])

if not models_ready:
    st.warning(
        "No trained model found. "
        "Run `python models/train_salary_model.py` first, then reload this page."
    )
    st.stop()

# BUG FIX: joblib.load can raise on corrupt / incompatible files — wrap in try/except.
try:
    model       = joblib.load(model_path)
    scaler      = joblib.load(scaler_path)
    feature_cols = joblib.load(cols_path)
except Exception as e:
    st.error(f"Failed to load model files: {e}")
    st.stop()

# Filter options

@st.cache_data
def load_options():
    roles = query(
        "SELECT DISTINCT job_title_short FROM jobs WHERE job_title_short IS NOT NULL ORDER BY job_title_short"
    )["job_title_short"].tolist()
    countries = query(
        "SELECT DISTINCT job_country FROM jobs WHERE job_country IS NOT NULL ORDER BY job_country"
    )["job_country"].tolist()
    skills = query(
        "SELECT DISTINCT skill FROM skills ORDER BY skill"
    )["skill"].tolist()
    return roles, countries, skills


roles, countries, all_skills = load_options()

# Input form

col1, col2 = st.columns(2)

with col1:
    role             = st.selectbox("Job Title", roles)
    country          = st.selectbox("Country", countries)
    selected_skills  = st.multiselect("Skills", all_skills)

with col2:
    is_remote        = st.checkbox("Remote", value=False)
    requires_degree  = st.checkbox("Degree Required", value=True)
    offers_insurance = st.checkbox("Health Insurance", value=False)

# Prediction

if st.button("Predict Salary", type="primary"):

    # Build a zeroed feature row
    row: dict[str, int | float] = {col: 0 for col in feature_cols}

    # Scalar features
    row["is_remote"]              = int(is_remote)
    row["requires_degree"]        = int(requires_degree)
    row["offers_health_insurance"] = int(offers_insurance)
    row["skill_count"]            = len(selected_skills)

    # One-hot: job title
    # BUG FIX: original dummy-encoding logic was broken — it compared suffix to
    # col_val (the full value) AND checked a second mismatched pattern.
    # Corrected to standard one-hot: find the column named f"job_title_short_{role}".
    role_col    = f"job_title_short_{role}"
    country_col = f"job_country_{country}"

    if role_col in row:
        row[role_col] = 1
    else:
        st.warning(
            f"Role '{role}' was not seen during training — prediction may be less accurate."
        )

    if country_col in row:
        row[country_col] = 1
    else:
        st.warning(
            f"Country '{country}' was not seen during training — prediction may be less accurate."
        )

    # One-hot: skills
    for skill in selected_skills:
        if skill in row:
            row[skill] = 1
        # Skills not in feature_cols are simply ignored (already 0)

    # Build DataFrame aligned to training columns
    input_df = pd.DataFrame([row])[feature_cols]

    # BUG FIX: scaler.transform expects a 2-D array — passing .values is fine,
    # but let's also guard against NaN columns that would break the scaler.
    if input_df.isnull().any().any():
        st.error("Feature vector contains NaN values — check feature_columns.joblib alignment.")
        st.stop()

    input_scaled = scaler.transform(input_df.values)

    # BUG FIX: model.predict returns an array; clip negative predictions to 0.
    pred = float(model.predict(input_scaled)[0])
    pred = max(pred, 0)

    st.success(f"Predicted Annual Salary: **${pred:,.0f}**")

    # Contextual note
    @st.cache_data
    def load_role_context(r: str):
        safe = r.replace("'", "''")
        return query(f"""
            SELECT COUNT(*) AS n, ROUND(AVG(salary_year_avg), 0) AS avg_sal
            FROM jobs
            WHERE job_title_short = '{safe}'
              AND salary_year_avg IS NOT NULL
        """)

    ctx = load_role_context(role)
    if not ctx.empty:
        c = ctx.iloc[0]
        n, avg_sal = c["n"], c["avg_sal"]
        if n and n > 0 and avg_sal:
            st.caption(
                f"Based on {int(n):,} '{role}' listings "
                f"with salary data (avg ${int(avg_sal):,}) in the training set."
            )

    # BUG FIX: show a confidence band using training-data percentiles
    # so the user understands the prediction range.
    @st.cache_data
    def load_salary_range(r: str):
        safe = r.replace("'", "''")
        return query(f"""
            SELECT
                PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY salary_year_avg) AS p25,
                PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY salary_year_avg) AS p75
            FROM jobs
            WHERE job_title_short = '{safe}'
              AND salary_year_avg IS NOT NULL
        """)

    rng = load_salary_range(role)
    if not rng.empty:
        p25, p75 = rng.iloc[0]["p25"], rng.iloc[0]["p75"]
        if p25 and p75:
            st.info(
                f"Typical salary range for {role}: **${p25:,.0f} – ${p75:,.0f}** "
                f"(25th–75th percentile from training data)"
            )