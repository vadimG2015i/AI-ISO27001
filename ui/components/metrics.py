"""Metric display cards and KPI widgets for Streamlit."""

import streamlit as st


def render_kpi_cards(
    overall_compliance: float,
    controls_assessed: int,
    total_controls: int,
    open_risks_count: int,
    critical_risks_count: int,
) -> None:
    """Renders top-level summary metrics row across 4 columns."""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(label="Overall Compliance", value=f"{overall_compliance:.1f}%")
    with col2:
        st.metric(label="Controls Assessed", value=f"{controls_assessed}/{total_controls}")
    with col3:
        st.metric(label="Open Risks", value=open_risks_count)
    with col4:
        st.metric(label="Critical Risks", value=critical_risks_count)

