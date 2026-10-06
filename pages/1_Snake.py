"""A browser-based Snake game linked to the accounting dashboard."""
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Snake", page_icon="🐍")
st.page_link("pages/0_Dashboard.py", label="Back to payment dashboard", icon="🏠")
st.title("🐍 Snake")
st.write("Eat the red apples and grow. Avoid the walls and your own tail.")
components.html(
    (Path(__file__).parent.parent / "snake.html").read_text(encoding="utf-8"),
    height=720,
)
