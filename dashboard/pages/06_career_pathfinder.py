import streamlit as st
import plotly.express as px

from dashboard.utils.db import query
from dashboard.utils.theme import apply_theme

apply_theme()

st.title("Career Pathfinder")


# Helpers

def themed(fig):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#ccc",
        margin=dict(t=40, b=20, l=10, r=10),
    )
    return fig


@st.cache_data
def load_roles():
    return query(
        "SELECT DISTINCT job_title_short FROM jobs WHERE job_title_short IS NOT NULL ORDER BY job_title_short"
    )["job_title_short"].tolist()


roles = load_roles()

if not roles:
    st.error("No role data found in the database.")
    st.stop()

target = st.selectbox("Select a Target Role", roles)

# Role KPIs

@st.cache_data
def load_role_stats(role: str):
    # BUG FIX: MEDIAN() is not standard SQL. Replaced with PERCENTILE_CONT.
    # SQLite alternative in comment below.
    safe_role = role.replace("'", "''")
    return query(f"""
        SELECT COUNT(*)                                                      AS job_count,
               ROUND(AVG(salary_year_avg), 0)                               AS avg_salary,
               ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP
                     (ORDER BY salary_year_avg), 0)                         AS median_salary
        FROM jobs
        WHERE job_title_short = '{safe_role}'
        -- SQLite: remove the PERCENTILE_CONT line and use AVG as approximation,
        -- or compute median in Python with pandas.
    """)


# BUG FIX: original used .iloc[0] directly on query result — crashes if empty.
role_df = load_role_stats(target)

if role_df.empty or role_df.iloc[0]["job_count"] == 0:
    st.warning(f"No data found for '{target}'.")
    st.stop()

role_stats = role_df.iloc[0]

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Job Postings", f"{role_stats['job_count']:,}")
with col2:
    avg = role_stats["avg_salary"]
    st.metric("Average Salary", f"${avg:,.0f}" if avg else "N/A")
with col3:
    med = role_stats["median_salary"]
    st.metric("Median Salary", f"${med:,.0f}" if med else "N/A")

st.divider()

# Skills & companies

@st.cache_data
def load_role_skills(role: str):
    safe_role = role.replace("'", "''")
    return query(f"""
        SELECT s.skill, COUNT(*) AS cnt
        FROM skills s
        JOIN jobs j ON s.job_id = j.job_id
        WHERE j.job_title_short = '{safe_role}'
        GROUP BY s.skill
        ORDER BY cnt DESC
        LIMIT 15
    """)


@st.cache_data
def load_role_companies(role: str):
    safe_role = role.replace("'", "''")
    return query(f"""
        SELECT company_name, COUNT(*) AS cnt
        FROM jobs
        WHERE job_title_short = '{safe_role}'
          AND company_name IS NOT NULL
        GROUP BY company_name
        ORDER BY cnt DESC
        LIMIT 10
    """)


col1, col2 = st.columns(2)

with col1:
    skills = load_role_skills(target)
    if not skills.empty:
        skills = skills.sort_values("cnt", ascending=True)
        fig = px.bar(
            skills,
            x="cnt",
            y="skill",
            orientation="h",
            title=f"Top Skills — {target}",
            labels={"cnt": "Job Listings", "skill": "Skill"},
        )
        st.plotly_chart(themed(fig), use_container_width=True)
    else:
        st.info(f"No skill data found for '{target}'.")

with col2:
    companies = load_role_companies(target)
    if not companies.empty:
        companies = companies.sort_values("cnt", ascending=True)
        fig = px.bar(
            companies,
            x="cnt",
            y="company_name",
            orientation="h",
            title=f"Top Hiring Companies — {target}",
            labels={"cnt": "Job Listings", "company_name": "Company"},
        )
        st.plotly_chart(themed(fig), use_container_width=True)
    else:
        st.info(f"No company data found for '{target}'.")

# Choropleth

@st.cache_data
def load_role_countries(role: str):
    safe_role = role.replace("'", "''")
    return query(f"""
        SELECT job_country, COUNT(*) AS cnt
        FROM jobs
        WHERE job_title_short = '{safe_role}'
          AND job_country IS NOT NULL
        GROUP BY job_country
        ORDER BY cnt DESC
    """)


countries = load_role_countries(target)

if not countries.empty:
    fig = px.choropleth(
        countries,
        locations="job_country",
        locationmode="country names",
        color="cnt",
        title=f"Countries Hiring — {target}",
        color_continuous_scale="Viridis",
        labels={"cnt": "Job Listings", "job_country": "Country"},
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        geo=dict(bgcolor="rgba(0,0,0,0)", showframe=False),
        font_color="#ccc",
        margin=dict(t=40, b=0, l=0, r=0),
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info(f"No country data found for '{target}'.")