import streamlit as st
import plotly.express as px

from dashboard.utils.db import query
from dashboard.utils.theme import apply_theme

apply_theme()

st.title("Remote Work Insights")


# Helpers

def themed(fig):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#ccc",
        margin=dict(t=40, b=20, l=10, r=10),
    )
    return fig


# Summary KPIs

@st.cache_data
def load_remote_summary():
    return query("""
        SELECT
            CASE WHEN is_remote = 1 THEN 'Remote' ELSE 'Onsite' END AS work_type,
            COUNT(*) AS job_count,
            ROUND(AVG(salary_year_avg), 0) AS avg_salary
        FROM jobs
        GROUP BY is_remote
    """)


remote_summary = load_remote_summary()

if remote_summary.empty:
    st.error("No remote work data available.")
    st.stop()

col1, col2 = st.columns(2)

with col1:
    fig = px.pie(
        remote_summary,
        names="work_type",
        values="job_count",
        title="Remote vs Onsite — Share of Listings",
        color_discrete_map={"Remote": "#636EFA", "Onsite": "#EF553B"},
    )
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#ccc")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    # BUG FIX: avg_salary can be NULL (no salary data for that work type).
    # Filter out null-salary rows before charting to avoid a blank bar.
    salary_cmp = remote_summary.dropna(subset=["avg_salary"])
    if not salary_cmp.empty:
        fig = px.bar(
            salary_cmp,
            x="work_type",
            y="avg_salary",
            title="Average Salary by Work Type",
            text_auto=",.0f",
            color="work_type",
            color_discrete_map={"Remote": "#636EFA", "Onsite": "#EF553B"},
            labels={"avg_salary": "Avg Annual Salary ($)", "work_type": "Work Type"},
        )
        st.plotly_chart(themed(fig), use_container_width=True)
    else:
        st.info("No salary data available for this comparison.")

# Remote trend over time

@st.cache_data
def load_remote_trend():
    # BUG FIX: SUM(is_remote) assumes is_remote is an integer.
    # If it's stored as BOOLEAN, cast it explicitly.
    return query("""
        SELECT
            DATE_TRUNC('month', job_posted_date) AS month,
            SUM(CAST(is_remote AS INTEGER))              AS remote_count,
            COUNT(*) - SUM(CAST(is_remote AS INTEGER))   AS onsite_count
        FROM jobs
        WHERE job_posted_date IS NOT NULL
        GROUP BY month
        ORDER BY month
    """)
    # SQLite alternative:
    # SELECT strftime('%Y-%m-01', job_posted_date) AS month, ...


remote_trend = load_remote_trend()

if not remote_trend.empty:
    fig = px.line(
        remote_trend,
        x="month",
        y=["remote_count", "onsite_count"],
        title="Remote vs Onsite Postings Over Time",
        labels={"value": "Job Count", "variable": "Work Type", "month": "Month"},
    )
    # BUG FIX: rename legend labels from raw column names to readable labels
    fig.for_each_trace(lambda t: t.update(
        name={"remote_count": "Remote", "onsite_count": "Onsite"}.get(t.name, t.name)
    ))
    st.plotly_chart(themed(fig), use_container_width=True)
else:
    st.info("No trend data available.")

# Remote % by country

@st.cache_data
def load_remote_by_country():
    return query("""
        SELECT
            job_country,
            COUNT(*) AS total,
            SUM(CAST(is_remote AS INTEGER)) AS remote,
            ROUND(100.0 * SUM(CAST(is_remote AS INTEGER)) / COUNT(*), 1) AS remote_pct
        FROM jobs
        WHERE job_country IS NOT NULL
        GROUP BY job_country
        HAVING COUNT(*) >= 5
        ORDER BY remote_pct DESC
        LIMIT 30
    """)


remote_by_country = load_remote_by_country()

if not remote_by_country.empty:
    # BUG FIX: sort ascending so highest-% country is at the top
    remote_by_country = remote_by_country.sort_values("remote_pct", ascending=True)
    fig = px.bar(
        remote_by_country,
        x="remote_pct",
        y="job_country",
        orientation="h",
        title="Remote Job % by Country (min 5 listings)",
        text_auto=True,
        hover_data=["total", "remote"],
        labels={"remote_pct": "Remote %", "job_country": "Country"},
    )
    st.plotly_chart(themed(fig), use_container_width=True)
else:
    st.info("Not enough country data to display.")