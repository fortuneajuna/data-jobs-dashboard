import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

EXPECTED_COLUMNS = [
    "job_title_short",
    "job_title",
    "job_location",
    "job_via",
    "job_schedule_type",
    "job_work_from_home",
    "search_location",
    "job_posted_date",
    "job_no_degree_mention",
    "job_health_insurance",
    "job_country",
    "salary_rate",
    "salary_year_avg",
    "salary_hour_avg",
    "company_name",
    "job_skills",
    "job_type_skills",
]


def extract_data(filepath: str) -> pd.DataFrame:
    """
    Load raw CSV data and validate schema.

    Args:
        filepath: Path to the CSV file

    Returns:
        DataFrame with raw data

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If schema validation fails
    """
    path = Path(filepath)

    if not path.exists():
        logger.error(f"File not found: {filepath}")
        raise FileNotFoundError(f"Data file not found: {filepath}")

    logger.info(f"Loading data from {filepath}")
    df = pd.read_csv(filepath)

    logger.info(f"Loaded {len(df)} rows, {len(df.columns)} columns")

    _validate_schema(df)

    _log_column_stats(df)

    return df


def _validate_schema(df: pd.DataFrame) -> None:
    """Validate that all expected columns are present."""
    missing = set(EXPECTED_COLUMNS) - set(df.columns)
    extra = set(df.columns) - set(EXPECTED_COLUMNS)

    if missing:
        logger.warning(f"Missing expected columns: {missing}")
    if extra:
        logger.info(f"Extra columns found: {extra}")

    if missing:
        raise ValueError(f"Schema validation failed. Missing columns: {missing}")


def _log_column_stats(df: pd.DataFrame) -> None:
    """Log basic statistics for each column."""
    for col in df.columns:
        null_count = df[col].isna().sum()
        null_pct = (null_count / len(df)) * 100
        dtype = df[col].dtype
        logger.info(f"  {col}: dtype={dtype}, nulls={null_count} ({null_pct:.1f}%)")