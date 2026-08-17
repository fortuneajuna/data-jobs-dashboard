import os
from pathlib import Path

import duckdb
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()


@st.cache_resource
def get_connection():
    db_path = os.getenv("DUCKDB_PATH", "data/processed/jobs.duckdb")
    full_path = Path(__file__).resolve().parent.parent.parent / db_path
    return duckdb.connect(str(full_path))


def query(sql: str) -> pd.DataFrame:
    conn = get_connection()
    return conn.execute(sql).fetchdf()
