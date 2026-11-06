"""Page 1: Compliance Document Upload & Text Ingestion."""

import streamlit as st

st.set_page_config(page_title="Document Upload | ISO 27001", page_icon="📁", layout="wide")

st.header("📁 Document Ingestion & Evidence Repository")
st.markdown(
    """
Upload your organization's security policies, operational procedures, architecture diagrams,
and asset inventories. Supported formats: **PDF, DOCX, XLSX** (up to 25 MB).
"""
)

st.info("Document upload pipeline and text extraction will be active in Phase 1.")

