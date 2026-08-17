import re
from pathlib import Path

import duckdb
import pytest

SQL_DIR = Path(__file__).resolve().parent.parent / "sql"
DB_PATH = Path("data/processed/jobs.duckdb")


@pytest.fixture
def conn():
    if not DB_PATH.exists():
        pytest.skip("No DuckDB database — run pipeline first")
    conn = duckdb.connect(str(DB_PATH))
    yield conn
    conn.close()


def get_query_blocks():
    with open(SQL_DIR / "analytics_queries.sql") as f:
        content = f.read()
    no_comments = re.sub(r"--.*", "", content)
    blocks = re.split(r"\n\s*\n", no_comments)
    return [b.strip() for b in blocks if b.strip()]


@pytest.mark.parametrize("block", get_query_blocks(), ids=lambda b: b[:40])
def test_analytics_query_executes(conn, block):
    result = conn.execute(block).fetchdf()
    assert isinstance(result, type(conn.execute("SELECT 1").fetchdf()))
