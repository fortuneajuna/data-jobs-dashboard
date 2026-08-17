import logging
from pathlib import Path

import duckdb
import joblib
import pandas as pd
from dotenv import load_dotenv
from mlxtend.frequent_patterns import apriori, association_rules

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

MODELS_DIR = Path(__file__).resolve().parent
DB_PATH = Path.cwd() / "data/processed/jobs.duckdb"


def load_skill_matrix() -> tuple[pd.DataFrame, pd.DataFrame]:
    conn = duckdb.connect(str(DB_PATH))
    df = conn.execute("""
        SELECT j.job_id, j.job_title_short, s.skill
        FROM jobs j JOIN skills s ON j.job_id = s.job_id
    """).fetchdf()
    conn.close()

    matrix = df.pivot_table(
        index="job_id", columns="skill", aggfunc="size", fill_value=0
    )
    matrix = (matrix > 0).astype(bool)
    return matrix, df[["job_id", "job_title_short"]].drop_duplicates()


def build_recommender():
    matrix, job_roles = load_skill_matrix()
    if matrix.empty:
        logger.warning("No skill data — skipping recommender")
        return

    frequent = apriori(
        matrix, min_support=0.05, use_colnames=True, max_len=3
    )
    if frequent.empty:
        logger.warning("No frequent itemsets found — saving empty rules")
        rules = pd.DataFrame()
    else:
        rules = association_rules(frequent, metric="lift", min_threshold=1.2)
        rules = rules.sort_values("lift", ascending=False)

    role_skills = (
        job_roles.groupby("job_title_short")["job_id"]
        .apply(list)
        .to_dict()
    )

    role_skill_sets = {}
    for role, job_ids in role_skills.items():
        if not job_ids:
            continue
        role_matrix = matrix.loc[matrix.index.isin(job_ids)]
        skill_counts = role_matrix.sum()
        top_skills = skill_counts[skill_counts > 0].sort_values(ascending=False).head(20)
        role_skill_sets[role] = top_skills.index.tolist()

    joblib.dump(rules, MODELS_DIR / "association_rules.joblib")
    joblib.dump(role_skill_sets, MODELS_DIR / "role_skills.joblib")
    logger.info(f"Saved {len(rules)} rules, {len(role_skill_sets)} roles")


def recommend_skills_for_role(role: str, top_n: int = 10) -> list[str]:
    try:
        role_skills = joblib.load(MODELS_DIR / "role_skills.joblib")
        return role_skills.get(role, [])[:top_n]
    except (FileNotFoundError, KeyError):
        return []


if __name__ == "__main__":
    build_recommender()
