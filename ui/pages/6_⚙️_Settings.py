"""Page 6: Settings, AI Provider Configuration & Standards Catalog."""

import streamlit as st

from iso_assistant.config import settings

st.set_page_config(page_title="Settings | ISO 27001", page_icon="⚙️", layout="wide")

st.header("⚙️ Application Settings & AI Configuration")
st.markdown(
    """
Configure system parameters, manage database storage, and select the AI analysis provider
(or operate 100% offline in mock mode).
"""
)

st.subheader("Current Runtime Configuration")
st.json(
    {
        "Application": settings.app_name,
        "Active AI Provider": settings.llm_provider,
        "Active Model": settings.llm_model,
        "Max Upload Size (MB)": settings.max_file_size_bytes / (1024 * 1024),
        "Allowed Extensions": settings.allowed_extensions,
        "Database URI": settings.database_url,
    }
)

