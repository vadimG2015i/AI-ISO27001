"""Unit tests for Statement of Applicability (SoA) data models."""

import pytest
from pydantic import ValidationError

from iso_assistant.soa.models import ImplementationStatus, JustificationCategory, SoAEntry


def test_valid_soa_entry():
    """Verify construction of valid Statement of Applicability record."""
    entry = SoAEntry(
        control_id="A.8.2",
        theme="Technological Controls (A.8)",
        title="Privileged access rights",
        is_applicable=True,
        justification_category=JustificationCategory.RISK_ASSESSMENT_TREATMENT,
        justification="Mandatory control to protect admin privileges on production infrastructure.",
        implementation_status=ImplementationStatus.IMPLEMENTED,
        responsible_role="Security Operations Lead",
    )
    assert entry.control_id == "A.8.2"
    assert entry.is_applicable is True
    assert entry.implementation_status == ImplementationStatus.IMPLEMENTED


def test_soa_entry_rejects_insufficient_justification():
    """Verify that justification requires meaningful explanation (minimum length check)."""
    with pytest.raises(ValidationError):
        SoAEntry(
            control_id="A.8.2",
            theme="Technological",
            title="Privileged access",
            is_applicable=True,
            justification="Too short",  # less than 10 characters
        )

