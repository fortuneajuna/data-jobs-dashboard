
from etl.pipeline import run_pipeline


def test_pipeline_end_to_end(temp_csv):
    run_pipeline(temp_csv)


def test_pipeline_output_shape(temp_csv):
    from etl.extract import extract_data
    from etl.transform import transform_data

    df = extract_data(temp_csv)
    jobs_df, skills_long_df = transform_data(df)
    assert len(jobs_df) > 0
    assert len(skills_long_df) > 0
    assert "job_id" in skills_long_df.columns or skills_long_df.columns.tolist() == ["job_id", "skill"]
