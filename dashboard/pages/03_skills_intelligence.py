import streamlit as st
import plotly.express as px
import networkx as nx
from streamlit.components.v1 import html

from dashboard.utils.db import query
from dashboard.utils.theme import apply_theme

apply_theme()

st.title("Skills Intelligence")


# Helpers

def themed(fig):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#ccc",
        margin=dict(t=40, b=20, l=10, r=10),
    )
    return fig


# Top skills & salary premium

col1, col2 = st.columns(2)

with col1:
    @st.cache_data
    def load_top_skills():
        return query("""
            SELECT skill, COUNT(*) AS demand_count
            FROM skills
            GROUP BY skill
            ORDER BY demand_count DESC
            LIMIT 20
        """)

    top_skills = load_top_skills()
    if not top_skills.empty:
        # BUG FIX: sort ascending so highest-demand skill is at top of horizontal bar
        top_skills = top_skills.sort_values("demand_count", ascending=True)
        fig = px.bar(
            top_skills,
            x="demand_count",
            y="skill",
            orientation="h",
            title="Top 20 Skills by Demand",
            labels={"demand_count": "Job Listings", "skill": "Skill"},
        )
        st.plotly_chart(themed(fig), use_container_width=True)
    else:
        st.warning("No skills data available.")

with col2:
    @st.cache_data
    def load_skill_premium():
        # BUG FIX: HAVING COUNT(*) >= 2 is too low for a salary premium — noisy results.
        # Raised to >= 10 for more reliable averages. Adjust to your dataset size.
        return query("""
            WITH overall AS (
                SELECT AVG(salary_year_avg) AS avg_all
                FROM jobs
                WHERE salary_year_avg IS NOT NULL
            )
            SELECT s.skill,
                   ROUND(AVG(j.salary_year_avg), 0)                           AS avg_with,
                   ROUND(AVG(j.salary_year_avg) - (SELECT avg_all FROM overall), 0) AS premium,
                   COUNT(*) AS listing_count
            FROM skills s
            JOIN jobs j ON s.job_id = j.job_id
            WHERE j.salary_year_avg IS NOT NULL
            GROUP BY s.skill
            HAVING COUNT(*) >= 10
            ORDER BY premium DESC
            LIMIT 20
        """)

    skill_premium = load_skill_premium()
    if not skill_premium.empty:
        skill_premium = skill_premium.sort_values("premium", ascending=True)
        fig = px.bar(
            skill_premium,
            x="premium",
            y="skill",
            orientation="h",
            title="Skill Salary Premium vs Overall Avg",
            color="premium",
            color_continuous_scale="RdYlGn",
            hover_data=["avg_with", "listing_count"],
            labels={"premium": "Salary Premium ($)", "skill": "Skill"},
        )
        st.plotly_chart(themed(fig), use_container_width=True)
    else:
        st.warning("Not enough salary data to compute skill premium.")

# Skill × Role heatmap

@st.cache_data
def load_skill_by_role():
    return query("""
        SELECT s.skill, j.job_title_short, COUNT(*) AS cnt
        FROM skills s
        JOIN jobs j ON s.job_id = j.job_id
        GROUP BY s.skill, j.job_title_short
    """)

skill_by_role = load_skill_by_role()

if not skill_by_role.empty:
    # BUG FIX: passing pivot.values loses axis labels — use the DataFrame directly.
    # Also limit to top-N skills by total demand to keep the heatmap readable.
    TOP_N = 30
    top_skill_names = (
        skill_by_role.groupby("skill")["cnt"]
        .sum()
        .nlargest(TOP_N)
        .index.tolist()
    )
    filtered = skill_by_role[skill_by_role["skill"].isin(top_skill_names)]
    pivot = filtered.pivot_table(
        index="skill", columns="job_title_short", values="cnt", fill_value=0
    )
    fig = px.imshow(
        pivot,                          # pass DataFrame, not .values
        title=f"Top {TOP_N} Skills — Demand by Role",
        aspect="auto",
        color_continuous_scale="Viridis",
        labels={"color": "Job Count"},
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="#ccc",
        margin=dict(t=50, b=20, l=10, r=10),
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("No skill-by-role data available.")

# Skill co-occurrence network

st.subheader("Skill Co-occurrence Network")

@st.cache_data
def load_cooccurrence():
    return query("""
        SELECT a.skill AS skill_a, b.skill AS skill_b, COUNT(*) AS strength
        FROM skills a
        JOIN skills b ON a.job_id = b.job_id AND a.skill < b.skill
        GROUP BY a.skill, b.skill
        ORDER BY strength DESC
        LIMIT 50
    """)

cooc = load_cooccurrence()

if not cooc.empty:
    # BUG FIX: pyvis import was buried inside an if-block with no graceful fallback.
    # Wrap in try/except so a missing pyvis package shows a clear message.
    try:
        from pyvis.network import Network

        G = nx.Graph()
        for _, row in cooc.iterrows():
            G.add_edge(row["skill_a"], row["skill_b"], weight=row["strength"])

        net = Network(height="500px", width="100%", bgcolor="#1e1e1e", font_color="white")
        net.set_options("""
        {
          "physics": { "stabilization": { "iterations": 100 } },
          "edges": { "smooth": false }
        }
        """)

        for node in G.nodes():
            degree = G.degree(node)
            net.add_node(node, label=node, size=max(10, degree * 5), title=f"Connections: {degree}")

        for u, v, d in G.edges(data=True):
            net.add_edge(u, v, value=d["weight"], title=f"Co-occurs {d['weight']} times")

        net_path = "/tmp/skills_network.html"
        net.save_graph(net_path)

        with open(net_path) as f:
            html(f.read(), height=520)

    except ImportError:
        st.warning(
            "The `pyvis` package is not installed. "
            "Run `pip install pyvis` and restart the app to see the network graph."
        )
else:
    st.info("Not enough co-occurrence data to build a network graph.")