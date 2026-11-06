"""Audit logging and change history module.

Provides non-repudiation and traceability for all ISO 27001 compliance activities:
- Document uploads and removals
- AI draft assessments and model metadata
- Human auditor reviews, overrides, approvals, and rejections
- Risk rating modifications and treatment changes
- Statement of Applicability inclusion/exclusion adjustments
"""

import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from iso_assistant.constants import AuditAction


class AuditLogger:
    """Manages creation and retrieval of compliance change history records."""

    @staticmethod
    def log_action(
        db: Session,
        project_id: str,
        action: AuditAction,
        entity_type: str,
        entity_id: str,
        performed_by: str,
        previous_state: dict[str, Any] | None = None,
        new_state: dict[str, Any] | None = None,
        comment: str | None = None,
    ) -> None:
        """Records a verifiable event in the audit history."""
        # Models will be imported lazily or through db models
        from iso_assistant.db.models import AuditLog

        record = AuditLog(
            project_id=project_id,
            action=action.value,
            entity_type=entity_type,
            entity_id=entity_id,
            performed_by=performed_by,
            previous_state=json.dumps(previous_state) if previous_state else None,
            new_state=json.dumps(new_state) if new_state else None,
            comment=comment,
            timestamp=datetime.now(UTC),
        )
        db.add(record)
        db.commit()

    @staticmethod
    def get_entity_history(
        db: Session,
        entity_type: str,
        entity_id: str,
    ) -> list[Any]:
        """Retrieves chronological history of changes for a specific compliance entity."""
        from iso_assistant.db.models import AuditLog

        return (
            db.query(AuditLog)
            .filter(AuditLog.entity_type == entity_type, AuditLog.entity_id == entity_id)
            .order_by(AuditLog.timestamp.desc())
            .all()
        )

