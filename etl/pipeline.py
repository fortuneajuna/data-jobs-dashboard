import argparse
import logging
import os

from dotenv import load_dotenv

from etl.extract import extract_data
from etl.transform import transform_data
from etl.load import load_to_duckdb

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("pipeline")


def run_pipeline(filepath: str) -> None:
    logger.info(f"Pipeline started — source: {filepath}")

    df = extract_data(filepath)
    jobs_df, skills_long_df = transform_data(df)
    job_count, skill_count = load_to_duckdb(jobs_df, skills_long_df)

    logger.info(
        f"Pipeline complete — {job_count} jobs, {skill_count} skills loaded"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Data Jobs ETL Pipeline")
    parser.add_argument(
        "--file",
        default=os.getenv("RAW_DATA_PATH", "data/raw/jobs.csv"),
        help="Path to raw CSV file",
    )
    args = parser.parse_args()
    run_pipeline(args.file)


if __name__ == "__main__":
    main()
