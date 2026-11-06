"""Page 5: Audit Reports & Package Exports."""

import streamlit as st

st.set_page_config(page_title="Reports & Export | ISO 27001", page_icon="📑", layout="wide")

st.header("📑 Compliance Reports & Export Packages")
st.markdown(
    """
Export the comprehensive compliance package into audit-ready formats:
- Multi-sheet Excel Audit Workbook (`.xlsx`) containing Gap Analysis, SoA, and Risk Register.
- Executive Summary Compliance Report (`.pdf`).
"""
)

st.info("Report export pipelines will be active in Phase 5.")

