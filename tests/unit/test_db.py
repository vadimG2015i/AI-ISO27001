"""Unit tests for SQLite database models and persistence."""

from sqlalchemy.orm import Session

from iso_assistant.constants import ComplianceStatus, ReviewStatus
from iso_assistant.db.models import GapAssessment, ISOControl, Project


def test_create_project_and_relationships(in_memory_db: Session):
    """Verify that Project, ISOControl, and GapAssessment entities can be persisted."""
    project = Project(
        name="Fintech Compliance Audit",
        organization_name="Fintech Global",
        scope_description="Payment Processing Gateway",
    )
    in_memory_db.add(project)
    in_memory_db.commit()

    control = ISOControl(
        id="A.5.15",
        category="Annex A",
        theme="Organizational Controls (A.5)",
        title="Access control",
        summary="Rules to control physical and logical access to information and other associated assets.",
    )
    in_memory_db.add(control)
    in_memory_db.commit()

    assessment = GapAssessment(
        project_id=project.id,
        control_id=control.id,
        review_status=ReviewStatus.AI_DRAFT.value,
        ai_status=ComplianceStatus.PARTIALLY_COMPLIANT.value,
        ai_compliance_score=0.5,
        ai_evidence_found="Access policy exists in uploaded documentation.",
        ai_identified_gaps="No annual access review records found.",
        ai_remediation_plan="Implement documented user access reviews.",
        ai_confidence_score=0.88,
    )
    in_memory_db.add(assessment)
    in_memory_db.commit()

    retrieved = in_memory_db.query(GapAssessment).filter_by(id=assessment.id).first()
    assert retrieved is not None
    assert retrieved.ai_compliance_score == 0.5
    assert retrieved.review_status == ReviewStatus.AI_DRAFT.value
    assert retrieved.human_status is None  # Human review pending

