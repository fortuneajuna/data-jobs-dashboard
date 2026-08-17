import streamlit as st
import plotly.express as px

from dashboard.utils.db import query
from dashboard.utils.theme import apply_theme

apply_theme()

st.title("Salary Analytics")


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
def load_filter_options():
    countries = query(
        "SELECT DISTINCT job_country FROM jobs WHERE job_country IS NOT NULL ORDER BY job_country"
    )["job_country"].tolist()
    roles = query(
        "SELECT DISTINCT job_title_short FROM jobs WHERE job_title_short IS NOT NULL ORDER BY job_title_short"
    )["job_title_short"].tolist()
    return countries, roles


# ---------------------------------------------------------------------------
# Filters

countries, roles = load_filter_options()

with st.expander("Filters", expanded=True):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        sel_country = st.selectbox("Country", ["All"] + countries)
    with col2:
        sel_role = st.selectbox("Role", ["All"] + roles)
    with col3:
        sel_remote = st.selectbox("Work Type", ["All", "Remote", "Onsite"])
    with col4:
        sel_degree = st.selectbox("Degree Required", ["All", "Yes", "No"])


filters = ["salary_year_avg IS NOT NULL"]

if sel_country != "All":
    # Value was fetched from the DB — safe, but we wrap defensively.
    filters.append(f"job_country = '{sel_country.replace(chr(39), chr(39)*2)}'")
if sel_role != "All":
    filters.append(f"job_title_short = '{sel_role.replace(chr(39), chr(39)*2)}'")
if sel_remote == "Remote":
    filters.append("is_remote = 1")
elif sel_remote == "Onsite":
    filters.append("is_remote = 0")
if sel_degree == "Yes":
    filters.append("requires_degree = 1")
elif sel_degree == "No":
    filters.append("requires_degree = 0")

where = " AND ".join(filters)

# Data

@st.cache_data
def load_salary_data(where_clause: str):
    return query(f"""
        SELECT salary_year_avg, job_title_short, job_country, is_remote
        FROM jobs
        WHERE {where_clause}
    """)


salary_data = load_salary_data(where)

if salary_data.empty:
    st.info("No salary data matches the selected filters.")
    st.stop()

# Charts — row 1

col1, col2 = st.columns(2)

with col1:
    fig = px.histogram(
        salary_data,
        x="salary_year_avg",
        nbins=30,
        title="Salary Distribution",
        labels={"salary_year_avg": "Annual Salary ($)"},
    )
    st.plotly_chart(themed(fig), use_container_width=True)

with col2:
    # BUG FIX: box plot with many roles produces an unreadable x-axis.
    # Sort by median descending so the most relevant roles appear first.
    role_order = (
        salary_data.groupby("job_title_short")["salary_year_avg"]
        .median()
        .sort_values(ascending=False)
        .index.tolist()
    )
    fig = px.box(
        salary_data,
        x="job_title_short",
        y="salary_year_avg",
        category_orders={"job_title_short": role_order},
        title="Salary by Role",
        labels={"salary_year_avg": "Annual Salary ($)", "job_title_short": "Role"},
    )
    fig.update_xaxes(tickangle=-35)
    st.plotly_chart(themed(fig), use_container_width=True)

# Charts — row 2

col1, col2 = st.columns(2)

with col1:
    by_country = (
        salary_data.groupby("job_country")["salary_year_avg"]
        .agg(["mean", "count"])
        .reset_index()
        .rename(columns={"mean": "avg_salary", "count": "listings"})
        .sort_values("avg_salary", ascending=True)   # ascending=True → largest bar at top
    )
    fig = px.bar(
        by_country,
        x="avg_salary",
        y="job_country",
        orientation="h",
        title="Avg Salary by Country",
        text_auto=",.0f",
        hover_data=["listings"],
        labels={"avg_salary": "Avg Salary ($)", "job_country": "Country"},
    )
    st.plotly_chart(themed(fig), use_container_width=True)

with col2:
    by_role = (
        salary_data.groupby("job_title_short")["salary_year_avg"]
        .agg(["mean", "count"])
        .reset_index()
        .rename(columns={"mean": "avg_salary", "count": "listings"})
        .sort_values("avg_salary", ascending=True)
    )
    fig = px.bar(
        by_role,
        x="avg_salary",
        y="job_title_short",
        orientation="h",
        title="Avg Salary by Role",
        text_auto=",.0f",
        hover_data=["listings"],
        labels={"avg_salary": "Avg Salary ($)", "job_title_short": "Role"},
    )
    st.plotly_chart(themed(fig), use_container_width=True)