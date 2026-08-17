import streamlit as st
import plotly.express as px

from dashboard.utils.db import query
from dashboard.utils.theme import apply_theme

apply_theme()

# Helpers

def themed_layout(fig, title: str = ""):
    """Apply a consistent dark-transparent theme to any Plotly figure."""
    fig.update_layout(
        title=title,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#ccc",
        margin=dict(t=40, b=20, l=10, r=10),
    )
    return fig


@st.cache_data
def load_kpis():
    # MEDIAN() is non-standard; use PERCENTILE_CONT (works in PostgreSQL/DuckDB).
    # If you're on SQLite, swap the PERCENTILE_CONT line for:
    #   AVG(salary_year_avg) AS median_salary   -- approximate only
    sql = """
    SELECT
        COUNT(*)                                                        AS total_jobs,
        ROUND(AVG(salary_year_avg), 0)                                  AS avg_salary,
        ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP
              (ORDER BY salary_year_avg), 0)                            AS median_salary,
        COUNT(DISTINCT job_country)                                     AS unique_countries,
        COUNT(DISTINCT company_name)                                    AS unique_companies,
        ROUND(SUM(CAST(is_remote AS INTEGER)) * 100.0 / COUNT(*), 1)   AS remote_pct
    FROM jobs
    """
    df = query(sql)
    return df.iloc[0] if not df.empty else None


@st.cache_data
def load_hiring_trend():
    # DATE_TRUNC is PostgreSQL; strftime is SQLite — pick whichever matches your DB.
    # PostgreSQL / DuckDB:
    sql = """
    SELECT DATE_TRUNC('month', job_posted_date) AS month,
           COUNT(*) AS jobs
    FROM jobs
    WHERE job_posted_date IS NOT NULL
    GROUP BY month
    ORDER BY month
    """
    # SQLite alternative (comment out the block above and uncomment below):
    # sql = """
    # SELECT strftime('%Y-%m-01', job_posted_date) AS month,
    #        COUNT(*) AS jobs
    # FROM jobs
    # WHERE job_posted_date IS NOT NULL
    # GROUP BY month
    # ORDER BY month
    # """
    return query(sql)


@st.cache_data
def load_top_roles():
    sql = """
    SELECT job_title_short, COUNT(*) AS cnt
    FROM jobs
    GROUP BY job_title_short
    ORDER BY cnt DESC
    LIMIT 10
    """
    return query(sql)


@st.cache_data
def load_salary_trend():
    sql = """
    SELECT DATE_TRUNC('month', job_posted_date) AS month,
           ROUND(AVG(salary_year_avg), 0) AS avg_salary
    FROM jobs
    WHERE salary_year_avg IS NOT NULL
      AND job_posted_date IS NOT NULL
    GROUP BY month
    ORDER BY month
    """
    return query(sql)


# Page

st.title("Executive Summary")

# ── KPI row ────────────────────────────────────────────────────────────────
row = load_kpis()

if row is None:
    st.error("Could not load KPI data — the jobs table may be empty.")
    st.stop()

k1, k2, k3, k4, k5, k6 = st.columns(6)

with k1:
    st.metric("Total Jobs", f"{row['total_jobs']:,.0f}")
with k2:
    avg = row["avg_salary"]
    st.metric("Avg Salary", f"${avg:,.0f}" if avg else "N/A")
with k3:
    med = row["median_salary"]
    st.metric("Median Salary", f"${med:,.0f}" if med else "N/A")
with k4:
    st.metric("Countries", f"{row['unique_countries']:,}")
with k5:
    st.metric("Companies", f"{row['unique_companies']:,}")
with k6:
    pct = row["remote_pct"]
    st.metric("Remote %", f"{pct:.1f}%" if pct is not None else "N/A")

st.divider()

# ── Charts row ─────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    hiring_trend = load_hiring_trend()
    if not hiring_trend.empty:
        fig = px.line(hiring_trend, x="month", y="jobs")
        themed_layout(fig, "Hiring Trend")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No hiring trend data available.")

with col2:
    top_roles = load_top_roles()
    if not top_roles.empty:
        # Sort ascending so largest bar is at the top of a horizontal chart
        top_roles = top_roles.sort_values("cnt", ascending=True)
        fig = px.bar(
            top_roles,
            x="cnt",
            y="job_title_short",
            orientation="h",
            labels={"cnt": "Number of Openings", "job_title_short": "Job Title"},
            color_discrete_sequence=["#636EFA"],
        )
        themed_layout(fig, "Top 10 Roles")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No role data available.")

# ── Salary trend (full width) ───────────────────────────────────────────────
salary_trend = load_salary_trend()
if not salary_trend.empty:
    fig = px.line(salary_trend, x="month", y="avg_salary",
                  labels={"avg_salary": "Avg Annual Salary ($)", "month": "Month"})
    themed_layout(fig, "Average Salary Trend")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("No salary trend data available.")