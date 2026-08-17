import os

import pandas as pd
import pytest

from etl.load import _read_schema, _get_connection, _create_tables, _load_jobs, _load_skills
from etl.transform import transform_data


def test_read_schema():
    sql = _read_schema()
    assert "CREATE TABLE" in sql
    assert "jobs" in sql
    assert "skills" in sql


@pytest.fixture
def db_conn(temp_db):
    os.environ["DUCKDB_PATH"] = temp_db
    conn = _get_connection()
    yield conn
    conn.close()
    os.environ.pop("DUCKDB_PATH", None)


def test_create_tables(db_conn):
    _create_tables(db_conn)
    tables = db_conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    table_names = [r[0] for r in tables]
    assert "jobs" in table_names
    assert "skills" in table_names


def test_load_jobs(sample_df, db_conn):
    jobs_df, _ = transform_data(sample_df)
    _create_tables(db_conn)
    count = _load_jobs(db_conn, jobs_df)
    assert count == 1
    row = db_conn.execute("SELECT job_title_short, salary_year_avg FROM jobs").fetchone()
    assert row[0] == "Data Engineer"


def test_load_skills(db_conn):
    _create_tables(db_conn)
    skills = pd.DataFrame({"job_id": [0, 0, 0], "skill": ["python", "sql", "spark"]})
    count = _load_skills(db_conn, skills)
    assert count == 3
