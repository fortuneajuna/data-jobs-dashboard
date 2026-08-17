import pandas as pd
import pytest

from etl.extract import extract_data, EXPECTED_COLUMNS


def test_extract_success(temp_csv):
    df = extract_data(temp_csv)
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
    for col in EXPECTED_COLUMNS:
        assert col in df.columns


def test_extract_raises_on_missing_file():
    with pytest.raises(FileNotFoundError):
        extract_data("/nonexistent/path.csv")


def test_extract_raises_on_missing_columns(temp_csv, sample_df):
    bad_csv = sample_df.drop(columns=["job_title_short"])
    bad_csv.to_csv(temp_csv, index=False)
    with pytest.raises(ValueError, match="Missing columns"):
        extract_data(temp_csv)


def test_extract_logs_column_stats(temp_csv, caplog):
    import logging
    caplog.set_level(logging.INFO)
    extract_data(temp_csv)
    assert any("job_title_short" in msg for msg in caplog.messages)
