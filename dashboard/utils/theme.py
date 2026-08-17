from pathlib import Path
import streamlit as st

_CSS_PATH = Path(__file__).resolve().parent.parent / "assets" / "style.css"

def apply_theme() -> None:
    """Inject the global stylesheet. Call once at the top of every page."""
    css = _CSS_PATH.read_text()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)