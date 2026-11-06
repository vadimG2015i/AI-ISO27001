"""Statement of Applicability (SoA) module for ISO/IEC 27001:2022."""

from iso_assistant.soa.models import ImplementationStatus, SoAEntry
from iso_assistant.soa.service import StatementOfApplicabilityService

__all__ = ["ImplementationStatus", "SoAEntry", "StatementOfApplicabilityService"]

