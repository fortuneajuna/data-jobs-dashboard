import streamlit as st

# ── MUST be the very first Streamlit call ──────────────────────────────────
st.set_page_config(
    page_title="Data Jobs Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Load shared CSS (once) ─────────────────────────────────────────────────
from dashboard.utils.theme import apply_theme
apply_theme()

# ── Sidebar branding ───────────────────────────────────────────────────────
st.sidebar.markdown(
    "<h1 style='text-align: center; margin-bottom: 1rem;'>📊 Data Jobs</h1>",
    unsafe_allow_html=True,
)
st.sidebar.markdown("---")