"""Page 4: Statement of Applicability (SoA) Management."""

import streamlit as st

st.set_page_config(page_title="Statement of Applicability | ISO 27001", page_icon="📋", layout="wide")

st.header("📋 ISO/IEC 27001:2022 Statement of Applicability (SoA)")
st.markdown(
    """
Manage the formal applicability status (Included vs. Excluded) and audit justifications for all
**93 Annex A controls**, fulfilling mandatory requirements of Clause 6.1.3.
"""
)

st.info("Statement of Applicability editor and audit tracker will be active in Phase 4.")

