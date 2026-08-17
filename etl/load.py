import logging
import os
from pathlib import Path

import duckdb
import pandas as pd
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "sql" / "schema.sql"


def _read_schema() -> str:
    with open(SCHEMA_PATH) as f:
        return f.read()


def _get_connection():
    token = os.getenv("MOTHERDUCK_TOKEN")
    if token:
        logger.info("Connecting to MotherDuck")
        return duckdb.connect(f"md:?motherduck_token={token}")
    db_path = os.getenv("DUCKDB_PATH", "data/processed/jobs.duckdb")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    logger.info(f"Connecting to local DuckDB at {db_path}")
    return duckdb.connect(db_path)


def _create_tables(conn: duckdb.DuckDBPyConnection) -> None:
    schema = _read_schema()
    conn.execute(schema)
    logger.info("Tables created / verified")


def _load_jobs(conn: duckdb.DuckDBPyConnection, df: pd.DataFrame) -> int:
    df = df.reset_index(drop=False)
    df = df.rename(columns={"index": "job_id"})

    col_map = {
        "job_title_short": "job_title_short",
        "job_title": "job_title",
        "job_location": "job_location",
        "job_via": "job_via",
        "job_schedule_type": "job_schedule_type",
        "job_country": "job_country",
        "company_name": "company_name",
        "search_location": "search_location",
        "salary_rate": "salary_rate",
        "salary_year_avg": "salary_year_avg",
        "salary_hour_avg": "salary_hour_avg",
        "salary_log": "salary_log",
        "is_remote": "is_remote",
        "requires_degree": "requires_degree",
        "offers_health_insurance": "offers_health_insurance",
        "job_work_from_home": "job_work_from_home",
        "job_no_degree_mention": "job_no_degree_mention",
        "job_health_insurance": "job_health_insurance",
        "job_posted_date": "job_posted_date",
        "days_since_posted": "days_since_posted",
        "skill_count": "skill_count",
    }

    df = df[["job_id"] + list(col_map.keys())]

    conn.execute("DELETE FROM jobs")
    conn.register("_jobs_df", df)
    conn.execute(
        f"INSERT INTO jobs ({', '.join(['job_id'] + list(col_map.values()))}) "
        f"SELECT * FROM _jobs_df"
    )
    result = conn.execute("SELECT count(*) FROM jobs").fetchone()
    count = result[0] if result else 0
    logger.info(f"Loaded {count} job records")
    return count


def _load_skills(conn: duckdb.DuckDBPyConnection, df: pd.DataFrame) -> int:
    conn.execute("DELETE FROM skills")
    conn.register("_skills_df", df)
    conn.execute("INSERT INTO skills SELECT * FROM _skills_df")
    result = conn.execute("SELECT count(*) FROM skills").fetchone()
    count = result[0] if result else 0
    logger.info(f"Loaded {count} skill records")
    return count


def load_to_duckdb(
    jobs_df: pd.DataFrame, skills_long_df: pd.DataFrame
) -> tuple[int, int]:
    conn = _get_connection()
    try:
        _create_tables(conn)
        job_count = _load_jobs(conn, jobs_df)
        skill_count = _load_skills(conn, skills_long_df)
        conn.commit()
        logger.info(f"Load complete: {job_count} jobs, {skill_count} skills")
        return job_count, skill_count
    except Exception:
        conn.rollback()
        logger.exception("Load failed, transaction rolled back")
        raise
    finally:
        conn.close()
