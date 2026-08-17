import os
import tempfile

import duckdb
import pandas as pd
import pytest

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


@pytest.fixture
def sample_row():
    return {
        "job_title_short": "Data Engineer",
        "job_title": "Senior Data Engineer",
        "job_location": "San Francisco, CA",
        "job_via": "LinkedIn",
        "job_schedule_type": "Full-time",
        "job_work_from_home": False,
        "search_location": "California, United States",
        "job_posted_date": "2023-06-15 10:00:00",
        "job_no_degree_mention": False,
        "job_health_insurance": True,
        "job_country": "United States",
        "salary_rate": "year",
        "salary_year_avg": 150000.0,
        "salary_hour_avg": None,
        "company_name": "Tech Corp",
        "job_skills": "['python', 'sql', 'spark']",
        "job_type_skills": "{'programming': ['python', 'sql'], 'libraries': ['spark']}",
    }


@pytest.fixture
def sample_df(sample_row):
    return pd.DataFrame([sample_row])


@pytest.fixture
def multi_row_df(sample_row):
    rows = [
        sample_row,
        {**sample_row, "job_title_short": "Data Scientist", "salary_year_avg": 130000.0},
        {**sample_row, "job_title_short": "Data Analyst", "salary_year_avg": 90000.0},
        {
            **sample_row,
            "job_title_short": "Data Analyst",
            "company_name": "Other Corp",
            "job_country": "Canada",
            "job_posted_date": "2023-07-01 08:00:00",
            "salary_year_avg": 85000.0,
        },
    ]
    return pd.DataFrame(rows)


@pytest.fixture
def temp_csv(sample_df):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        sample_df.to_csv(f, index=False)
        path = f.name
    yield path
    os.unlink(path)


@pytest.fixture
def temp_db():
    tmp = tempfile.NamedTemporaryFile(suffix=".duckdb", delete=False)
    tmp.close()
    os.unlink(tmp.name)
    conn = duckdb.connect(tmp.name)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            job_id BIGINT, job_title_short VARCHAR, job_title VARCHAR,
            job_location VARCHAR, job_via VARCHAR, job_schedule_type VARCHAR,
            job_country VARCHAR, company_name VARCHAR, search_location VARCHAR,
            salary_rate VARCHAR, salary_year_avg DOUBLE, salary_hour_avg DOUBLE,
            salary_log DOUBLE, is_remote BOOLEAN, requires_degree BOOLEAN,
            offers_health_insurance BOOLEAN, job_work_from_home BOOLEAN,
            job_no_degree_mention BOOLEAN, job_health_insurance BOOLEAN,
            job_posted_date TIMESTAMP WITH TIME ZONE, days_since_posted INTEGER,
            skill_count INTEGER, loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS skills (
            job_id BIGINT, skill VARCHAR
        )
    """)
    conn.close()
    yield tmp.name
    os.unlink(tmp.name)
