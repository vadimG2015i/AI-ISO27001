"""ISO 27001 Gap Analysis service separating AI drafts from human approvals."""

from sqlalchemy.orm import Session

from iso_assistant.ai.client import AIClient
from iso_assistant.constants import ComplianceStatus
from iso_assistant.db.models import GapAssessment


class GapAnalysisService:
    """Evaluates compliance evidence against ISO 27001:2022 clauses and Annex A controls."""

    def __init__(self, ai_client: AIClient | None = None):
        self.ai_client = ai_client or AIClient()

    def run_ai_assessment_for_control(
        self,
        db: Session,
        project_id: str,
        control_id: str,
        evidence_text: str,
    ) -> GapAssessment:
        """Executes an AI-driven compliance evaluation for an individual control.

        Stores finding with ReviewStatus.AI_DRAFT, keeping AI inferences strictly
        separated from human audit decisions until verified.
        """
        # Placeholder skeleton pending business logic implementation
        raise NotImplementedError("AI gap assessment logic will be implemented in Phase 2.")

    @staticmethod
    def approve_human_assessment(
        db: Session,
        project_id: str,
        control_id: str,
        reviewer_name: str,
        status: ComplianceStatus,
        compliance_score: float,
        notes: str,
    ) -> GapAssessment:
        """Records a human auditor's formal review, override, or approval of an assessment.

        Transitions assessment lifecycle state to ReviewStatus.APPROVED_HUMAN
        and creates a verifiable audit log entry.
        """
        # Placeholder skeleton pending business logic implementation
        raise NotImplementedError("Human review approval logic will be implemented in Phase 2.")

    @staticmethod
    def get_compliance_metrics(db: Session, project_id: str) -> dict[str, float]:
        """Calculates compliance percentages across Management Clauses and Annex A domains."""
        # Placeholder skeleton pending business logic implementation
        raise NotImplementedError("Compliance metrics calculation will be implemented in Phase 2.")

