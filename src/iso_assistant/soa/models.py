"""Domain models and schemas for Statement of Applicability (SoA)."""

from enum import Enum

from pydantic import BaseModel, Field


class ImplementationStatus(str, Enum):
    """Maturity status of an applicable ISO 27001 control."""

    IMPLEMENTED = "Implemented"
    IN_PROGRESS = "In Progress"
    PLANNED = "Planned"
    NOT_IMPLEMENTED = "Not Implemented"


class JustificationCategory(str, Enum):
    """Standardized audit justification rationale under ISO 27001 Clause 6.1.3."""

    RISK_ASSESSMENT_TREATMENT = "Risk Assessment / Risk Treatment"
    LEGAL_REGULATORY_REQUIREMENT = "Legal / Statutory / Regulatory Requirement"
    CONTRACTUAL_OBLIGATION = "Contractual / Client Obligation"
    BUSINESS_BEST_PRACTICE = "Business Requirement & Security Best Practice"
    OUT_OF_SCOPE_PHYSICAL = "Excluded: Organization operates 100% remote / cloud-hosted"
    OUT_OF_SCOPE_DEVELOPMENT = "Excluded: No custom software development conducted"
    OUT_OF_SCOPE_OTHER = "Excluded: Explicitly justified by management risk acceptance"


class SoAEntry(BaseModel):
    """Schema representing an individual Annex A control's Statement of Applicability."""

    control_id: str
    theme: str
    title: str
    is_applicable: bool = True
    justification_category: JustificationCategory = JustificationCategory.RISK_ASSESSMENT_TREATMENT
    justification: str = Field(..., min_length=10, description="Defensible audit rationale for inclusion or exclusion")
    implementation_status: ImplementationStatus = ImplementationStatus.PLANNED
    responsible_role: str | None = None
    target_date: str | None = None
    auditor_verified: bool = False
    verified_by: str | None = None

