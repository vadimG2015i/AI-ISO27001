"""Page 3: Information Security Risk Register & 5x5 Heatmap."""

import streamlit as st

st.set_page_config(page_title="Risk Register | ISO 27001", page_icon="🛡️", layout="wide")

st.header("🛡️ ISO/IEC 27005 Information Security Risk Register")
st.markdown(
    """
Manage organizational risks, analyze inherent vs. residual scores using an interactive $5 \\times 5$
likelihood and impact matrix, and map treatments directly to ISO 27001:2022 controls.
"""
)

st.info("Interactive risk register and Plotly heatmap will be active in Phase 4.")

