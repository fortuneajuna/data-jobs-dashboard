import streamlit as st
import plotly.express as px

from dashboard.utils.db import query
from dashboard.utils.theme import apply_theme

apply_theme()

st.title("Company Insights")


# Helpers

def themed(fig):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#ccc",
        margin=dict(t=40, b=20, l=10, r=10),
    )
    return fig


# Top hiring & top paying

@st.cache_data
def load_top_hiring():
    return query("""
        SELECT company_name, COUNT(*) AS job_count
        FROM jobs
        WHERE company_name IS NOT NULL
        GROUP BY company_name
        ORDER BY job_count DESC
        LIMIT 15
    """)


@st.cache_data
def load_top_paying():
    # BUG FIX: ranking by avg_salary with no minimum listing count produces
    # one-off companies that posted a single high-paying role — misleading.
    # Added HAVING COUNT(*) >= 3 for fairer comparison.
    return query("""
        SELECT company_name,
               ROUND(AVG(salary_year_avg), 0) AS avg_salary,
               COUNT(*) AS job_count
        FROM jobs
        WHERE salary_year_avg IS NOT NULL
          AND company_name IS NOT NULL
        GROUP BY company_name
        HAVING COUNT(*) >= 3
        ORDER BY avg_salary DESC
        LIMIT 15
    """)


col1, col2 = st.columns(2)

with col1:
    top_hiring = load_top_hiring()
    if not top_hiring.empty:
        top_hiring = top_hiring.sort_values("job_count", ascending=True)
        fig = px.bar(
            top_hiring,
            x="job_count",
            y="company_name",
            orientation="h",
            title="Top 15 Hiring Companies",
            labels={"job_count": "Job Postings", "company_name": "Company"},
        )
        st.plotly_chart(themed(fig), use_container_width=True)
    else:
        st.warning("No hiring data available.")

with col2:
    top_paying = load_top_paying()
    if not top_paying.empty:
        top_paying = top_paying.sort_values("avg_salary", ascending=True)
        fig = px.bar(
            top_paying,
            x="avg_salary",
            y="company_name",
            orientation="h",
            title="Highest Paying Companies (min 3 listings)",
            text_auto=",.0f",
            hover_data=["job_count"],
            labels={"avg_salary": "Avg Salary ($)", "company_name": "Company"},
        )
        st.plotly_chart(themed(fig), use_container_width=True)
    else:
        st.warning("Not enough salary data to rank companies.")

# Most remote-friendly companies

@st.cache_data
def load_remote_friendly():
    return query("""
        SELECT company_name,
               COUNT(*) AS total,
               SUM(CAST(is_remote AS INTEGER)) AS remote,
               ROUND(100.0 * SUM(CAST(is_remote AS INTEGER)) / COUNT(*), 1) AS remote_pct
        FROM jobs
        WHERE company_name IS NOT NULL
        GROUP BY company_name
        HAVING COUNT(*) >= 5
        ORDER BY remote_pct DESC
        LIMIT 15
    """)
   


remote_friendly = load_remote_friendly()

if not remote_friendly.empty:
    remote_friendly = remote_friendly.sort_values("remote_pct", ascending=True)
    fig = px.bar(
        remote_friendly,
        x="remote_pct",
        y="company_name",
        orientation="h",
        title="Most Remote-Friendly Companies (min 5 listings)",
        text_auto=True,
        hover_data=["total", "remote"],
        labels={"remote_pct": "Remote %", "company_name": "Company"},
    )
    st.plotly_chart(themed(fig), use_container_width=True)
else:
    st.info("Not enough data to rank remote-friendly companies.")