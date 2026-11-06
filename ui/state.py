"""Session state management and page context helpers for Streamlit."""

from typing import Any

import streamlit as st


def init_session_state() -> None:
    """Initializes default Streamlit session state keys."""
    defaults: dict[str, Any] = {
        "active_project_id": None,
        "current_user_name": "Compliance Officer",
        "current_user_role": "Compliance Officer",
        "selected_theme_filter": "All",
        "selected_status_filter": "All",
        "last_refresh_timestamp": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def get_current_project_id() -> str | None:
    """Returns currently selected compliance project ID."""
    return st.session_state.get("active_project_id")


def set_current_project_id(project_id: str) -> None:
    """Updates active compliance project ID in session state."""
    st.session_state["active_project_id"] = project_id

