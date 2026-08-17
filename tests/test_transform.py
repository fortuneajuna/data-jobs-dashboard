import pandas as pd

from etl.transform import (
    transform_data,
    _remove_duplicates,
    _standardize_countries,
    _standardize_companies,
    _parse_dates,
    _convert_salaries,
    _handle_missing_data,
    _engineer_features,
    _normalize_skills,
)


def test_remove_duplicates(multi_row_df):
    result = _remove_duplicates(multi_row_df)
    assert len(result) < len(multi_row_df)
    assert result.duplicated(subset=["job_title", "company_name", "job_location", "job_posted_date"]).sum() == 0


def test_standardize_countries(sample_df):
    result = _standardize_countries(sample_df)
    assert result["job_country"].iloc[0] == "United States"


def test_standardize_countries_unknown(sample_df):
    sample_df["job_country"] = "Narnia"
    result = _standardize_countries(sample_df)
    assert result["job_country"].iloc[0] == "Narnia"


def test_standardize_companies(sample_df):
    sample_df["company_name"] = "Acme Corp, Inc."
    result = _standardize_companies(sample_df)
    assert result["company_name"].iloc[0] == "Acme"


def test_parse_dates(sample_df):
    result = _parse_dates(sample_df)
    assert result["job_posted_date"].dtype.kind == "M"


def test_convert_salaries(sample_df):
    result = _convert_salaries(sample_df)
    assert result["salary_year_avg"].iloc[0] == 150000.0


def test_convert_salaries_hourly(sample_df):
    sample_df["salary_year_avg"] = None
    sample_df["salary_hour_avg"] = 50.0
    sample_df["salary_rate"] = "hour"
    result = _convert_salaries(sample_df)
    assert result["salary_year_avg"].iloc[0] == 50.0 * 2080


def test_handle_missing_data(sample_df):
    sample_df["job_skills"] = None
    sample_df["job_work_from_home"] = None
    sample_df["job_no_degree_mention"] = None
    sample_df["job_health_insurance"] = None
    result = _handle_missing_data(sample_df)
    assert result["job_skills"].iloc[0] == "[]"
    assert not result["job_work_from_home"].iloc[0]
    assert result["job_no_degree_mention"].iloc[0]
    assert not result["job_health_insurance"].iloc[0]


def test_engineer_features(sample_df):
    sample_df = _parse_dates(sample_df)
    sample_df = _engineer_features(sample_df)
    assert "salary_log" in sample_df.columns
    assert "days_since_posted" in sample_df.columns
    assert "skill_count" in sample_df.columns
    assert "is_remote" in sample_df.columns
    assert sample_df["skill_count"].iloc[0] == 3


def test_normalize_skills(sample_df):
    job_df, skills_df = _normalize_skills(sample_df)
    assert len(skills_df) == 3
    assert list(skills_df["skill"]) == ["python", "sql", "spark"]


def test_normalize_skills_empty():
    df = pd.DataFrame({"job_skills": ["[]"]})
    _, skills_df = _normalize_skills(df)
    assert len(skills_df) == 0


def test_transform_data(multi_row_df):
    jobs_df, skills_long_df = transform_data(multi_row_df)
    assert isinstance(jobs_df, pd.DataFrame)
    assert isinstance(skills_long_df, pd.DataFrame)
    assert len(jobs_df) > 0
    assert "salary_log" in jobs_df.columns
    assert "skill" in skills_long_df.columns
