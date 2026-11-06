"""Main Streamlit application entry point for AI ISO 27001 Compliance Assistant.

Responsibilities:
- Configure page title, layout, and theme.
- Initialize database schema on startup if needed.
- Provide high-level Executive Compliance Dashboard.
- Provide global navigation sidebar across audit phases.
"""

import streamlit as st

# Configure page layout
st.set_page_config(
    page_title="AI ISO 27001 Compliance Assistant",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🛡️ AI ISO/IEC 27001:2022 Compliance Assistant")
st.markdown(
    """
Welcome to the **AI ISO 27001 Compliance Assistant**. This platform streamlines Information Security
Management System (ISMS) compliance readiness, gap analyses, and risk registers.

### Compliance Workflow
1. **📁 Document Upload:** Ingest security policies, procedures, and asset registers (PDF, DOCX, XLSX).
2. **📊 Gap Analysis:** Review AI-generated gap evaluations and record formal human auditor approvals.
3. **🛡️ Risk Register:** Discover threats, analyze inherent/residual scores on a $5 \\times 5$ matrix, and track treatments.
4. **📋 Statement of Applicability (SoA):** Maintain defensible inclusion/exclusion justifications for all 93 controls.
5. **📑 Reports & Export:** Generate audit-ready Excel packages and executive PDF summaries.
6. **⚙️ Settings:** Configure LLM backends (or operate offline in mock mode) and inspect standards.
"""
)

st.info("System initialized in foundation mode. Business logic and UI workflows will be activated in upcoming phases.")

