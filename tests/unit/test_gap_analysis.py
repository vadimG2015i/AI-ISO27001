"""Unit tests verifying separation between AI drafts and Human auditor reviews."""

from iso_assistant.constants import ComplianceStatus, ReviewStatus
from iso_assistant.db.models import GapAssessment


def test_gap_assessment_state_separation():
    """Verify that AI Draft attributes and Human Approved attributes are distinct fields."""
    assessment = GapAssessment(
        project_id="sample-proj-id",
        control_id="A.5.1",
        review_status=ReviewStatus.AI_DRAFT.value,
        ai_status=ComplianceStatus.PARTIALLY_COMPLIANT.value,
        ai_compliance_score=0.5,
        ai_evidence_found="AI found evidence in section 3.1.",
        # Human approval fields are initially unset
        human_status=None,
        human_compliance_score=None,
        approved_by=None,
        approved_at=None,
    )

    assert assessment.review_status == ReviewStatus.AI_DRAFT.value
    assert assessment.approved_by is None

    # Simulate Human Auditor Override / Approval
    assessment.human_status = ComplianceStatus.COMPLIANT.value
    assessment.human_compliance_score = 1.0
    assessment.human_notes = "Auditor verified external ticket demonstrating active review."
    assessment.approved_by = "Lead Auditor"
    assessment.review_status = ReviewStatus.APPROVED_HUMAN.value

    # AI record remains intact for audit traceability
    assert assessment.ai_status == ComplianceStatus.PARTIALLY_COMPLIANT.value
    assert assessment.human_status == ComplianceStatus.COMPLIANT.value
    assert assessment.review_status == ReviewStatus.APPROVED_HUMAN.value

