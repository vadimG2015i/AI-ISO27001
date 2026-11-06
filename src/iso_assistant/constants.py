"""Domain constants and enumerations for ISO/IEC 27001:2022 Compliance.

Note: In accordance with copyright compliance, this module contains only public
taxonomies, structural clause numbers, standard control identifiers, and domain enums.
No copyrighted verbatim standard text is contained here.
"""

from enum import Enum


class StandardClause(str, Enum):
    """Mandatory Management System clauses in ISO/IEC 27001:2022."""

    CLAUSE_4 = "Clause 4: Context of the Organization"
    CLAUSE_5 = "Clause 5: Leadership"
    CLAUSE_6 = "Clause 6: Planning"
    CLAUSE_7 = "Clause 7: Support"
    CLAUSE_8 = "Clause 8: Operation"
    CLAUSE_9 = "Clause 9: Performance Evaluation"
    CLAUSE_10 = "Clause 10: Improvement"


class AnnexATheme(str, Enum):
    """The 4 reorganized control themes of ISO/IEC 27001:2022 Annex A."""

    ORGANIZATIONAL = "Organizational Controls (A.5)"
    PEOPLE = "People Controls (A.6)"
    PHYSICAL = "Physical Controls (A.7)"
    TECHNOLOGICAL = "Technological Controls (A.8)"


class ComplianceStatus(str, Enum):
    """Compliance assessment result for an individual control or clause."""

    COMPLIANT = "Compliant"
    PARTIALLY_COMPLIANT = "Partially Compliant"
    NON_COMPLIANT = "Non-Compliant"
    NOT_APPLICABLE = "Not Applicable"


class ReviewStatus(str, Enum):
    """Lifecycle state separating AI-generated assessments from human approvals."""

    AI_DRAFT = "AI Draft"
    UNDER_REVIEW = "Under Review"
    APPROVED_HUMAN = "Human Approved"
    REJECTED_HUMAN = "Human Rejected"


class RiskTreatmentStrategy(str, Enum):
    """ISO 27005 / ISO 31000 aligned risk treatment strategies."""

    MITIGATE = "Mitigate"
    AVOID = "Avoid"
    TRANSFER = "Transfer"
    ACCEPT = "Accept"


class CIAProperty(str, Enum):
    """Information security properties."""

    CONFIDENTIALITY = "Confidentiality"
    INTEGRITY = "Integrity"
    AVAILABILITY = "Availability"
    CONFIDENTIALITY_INTEGRITY = "Confidentiality & Integrity"
    ALL = "Confidentiality, Integrity & Availability"


class AuditAction(str, Enum):
    """Action types recorded in the tamper-evident audit log."""

    DOCUMENT_UPLOAD = "DOCUMENT_UPLOAD"
    DOCUMENT_DELETE = "DOCUMENT_DELETE"
    ASSESSMENT_AI_GENERATED = "ASSESSMENT_AI_GENERATED"
    ASSESSMENT_HUMAN_APPROVED = "ASSESSMENT_HUMAN_APPROVED"
    ASSESSMENT_HUMAN_REVISED = "ASSESSMENT_HUMAN_REVISED"
    RISK_CREATED = "RISK_CREATED"
    RISK_UPDATED = "RISK_UPDATED"
    SOA_DECISION_UPDATED = "SOA_DECISION_UPDATED"


class RiskLevel(str, Enum):
    """Qualitative risk categorization based on inherent/residual score."""

    VERY_LOW = "Very Low"    # 1 - 4
    LOW = "Low"              # 5 - 8
    MEDIUM = "Medium"        # 9 - 14
    HIGH = "High"            # 15 - 19
    CRITICAL = "Critical"    # 20 - 25


def calculate_risk_level(score: int) -> RiskLevel:
    """Classify a 1-25 risk score into a qualitative risk band."""
    if score >= 20:
        return RiskLevel.CRITICAL
    if score >= 15:
        return RiskLevel.HIGH
    if score >= 9:
        return RiskLevel.MEDIUM
    if score >= 5:
        return RiskLevel.LOW
    return RiskLevel.VERY_LOW

