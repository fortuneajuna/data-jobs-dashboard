import ast
import logging
import re

import numpy as np
import pandas as pd
import pycountry

logger = logging.getLogger(__name__)


def transform_data(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Transform raw job data into clean, feature-rich format.

    Args:
        df: Raw DataFrame from extract step

    Returns:
        Tuple of (jobs_df, skills_long_df) where:
        - jobs_df: Cleaned job records with engineered features
        - skills_long_df: Normalized skills (job_id, skill)
    """
    logger.info("Starting data transformation")

    df = df.copy()

    df = _remove_duplicates(df)
    df = _standardize_countries(df)
    df = _standardize_companies(df)
    df = _parse_dates(df)
    df = _convert_salaries(df)
    df = _handle_missing_data(df)
    df = _engineer_features(df)

    jobs_df, skills_long_df = _normalize_skills(df)

    logger.info(f"Transformation complete: {len(jobs_df)} jobs, {len(skills_long_df)} skill records")

    return jobs_df, skills_long_df


def _remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Remove duplicate job postings."""
    initial = len(df)
    df = df.drop_duplicates(subset=["job_title", "company_name", "job_location", "job_posted_date"])
    removed = initial - len(df)
    if removed:
        logger.info(f"Removed {removed} duplicate records")
    return df


def _standardize_countries(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize country names using pycountry."""
    def normalize_country(name: str) -> str:
        if pd.isna(name):
            return "Unknown"
        try:
            country = pycountry.countries.lookup(name)
            return country.name
        except LookupError:
            return name

    df["job_country"] = df["job_country"].apply(normalize_country)
    return df


def _standardize_companies(df: pd.DataFrame) -> pd.DataFrame:
    """Basic company name standardization."""
    def clean_company(name: str) -> str:
        if pd.isna(name):
            return "Unknown"
        name = re.sub(r"\s+", " ", name.strip())
        name = re.sub(r",?\s*Inc\.?$", "", name, flags=re.IGNORECASE)
        name = re.sub(r",?\s*LLC\.?$", "", name, flags=re.IGNORECASE)
        name = re.sub(r",?\s*Ltd\.?$", "", name, flags=re.IGNORECASE)
        name = re.sub(r",?\s*Corp\.?$", "", name, flags=re.IGNORECASE)
        return name.strip()

    df["company_name"] = df["company_name"].apply(clean_company)
    return df


def _parse_dates(df: pd.DataFrame) -> pd.DataFrame:
    """Parse job_posted_date to datetime."""
    df["job_posted_date"] = pd.to_datetime(df["job_posted_date"], errors="coerce", utc=True)
    null_dates = df["job_posted_date"].isna().sum()
    if null_dates:
        logger.warning(f"{null_dates} rows have unparseable dates")
    return df


def _convert_salaries(df: pd.DataFrame) -> pd.DataFrame:
    """Convert salary columns to numeric."""
    for col in ["salary_year_avg", "salary_hour_avg"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["salary_year_avg"] = df.apply(_normalize_salary, axis=1)  # type: ignore[call-overload]

    return df


def _normalize_salary(row: pd.Series) -> float | None:
    """Normalize salary to annual based on salary_rate."""
    if pd.notna(row["salary_year_avg"]):
        return row["salary_year_avg"]

    if pd.notna(row["salary_hour_avg"]) and row["salary_rate"] == "hour":
        return row["salary_hour_avg"] * 2080

    return None


def _handle_missing_data(df: pd.DataFrame) -> pd.DataFrame:
    """Handle missing values with documented assumptions."""
    df["job_skills"] = df["job_skills"].fillna("[]")
    df["job_type_skills"] = df["job_type_skills"].fillna("{}")

    df["job_work_from_home"] = df["job_work_from_home"].fillna(False).astype(bool)
    df["job_no_degree_mention"] = df["job_no_degree_mention"].fillna(True).astype(bool)
    df["job_health_insurance"] = df["job_health_insurance"].fillna(False).astype(bool)

    df["salary_rate"] = df["salary_rate"].fillna("year")

    return df


def _engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create engineered features."""
    df["salary_log"] = df["salary_year_avg"].apply(lambda x: np.log(x) if pd.notna(x) and x > 0 else None)

    ref_date = df["job_posted_date"].max()
    df["days_since_posted"] = (ref_date - df["job_posted_date"]).dt.days

    df["skill_count"] = df["job_skills"].apply(_count_skills)

    df["is_remote"] = df["job_work_from_home"].astype(int)
    df["requires_degree"] = (~df["job_no_degree_mention"]).astype(int)
    df["offers_health_insurance"] = df["job_health_insurance"].astype(int)

    return df


def _count_skills(skills_str: str) -> int:
    """Count skills from stringified list."""
    try:
        skills = ast.literal_eval(skills_str)
        if isinstance(skills, list):
            return len(skills)
    except (ValueError, SyntaxError):
        pass
    return 0


def _normalize_skills(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Convert skill lists to normalized long format."""
    skills_records = []

    for idx, row in df.iterrows():
        job_id = idx
        try:
            skills = ast.literal_eval(row["job_skills"])
            if isinstance(skills, list):
                for skill in skills:
                    if skill and isinstance(skill, str):
                        skills_records.append({"job_id": job_id, "skill": skill.strip().lower()})
        except (ValueError, SyntaxError):
            pass

    skills_long_df = pd.DataFrame(skills_records).drop_duplicates()

    return df, skills_long_df