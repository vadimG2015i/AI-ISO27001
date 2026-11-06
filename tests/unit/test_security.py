"""Unit tests for file upload security, magic byte validation, and audit logging."""

from sqlalchemy.orm import Session

from iso_assistant.constants import AuditAction
from iso_assistant.db.models import Project
from iso_assistant.security.audit_logger import AuditLogger
from iso_assistant.security.file_validator import FileValidator


def test_sanitize_filename_prevents_traversal():
    """Verify that dangerous directory traversal tokens and characters are neutralized."""
    dangerous = "../../etc/passwd/malicious.pdf"
    sanitized = FileValidator.sanitize_filename(dangerous)
    assert ".." not in sanitized
    assert "/" not in sanitized
    assert "\\" not in sanitized
    assert sanitized.endswith(".pdf")


def test_empty_file_rejected():
    """Verify that 0-byte uploads are flagged as invalid."""
    res = FileValidator.validate_file("empty.pdf", b"")
    assert not res.is_valid
    assert "empty" in res.error_message.lower()


def test_magic_bytes_detection_prevents_spoofing():
    """Verify that an executable or text file renamed to .pdf is blocked by magic byte check."""
    fake_pdf = b"Plain text payload pretending to be a PDF"
    res = FileValidator.validate_file("fake.pdf", fake_pdf)
    assert not res.is_valid
    assert "header mismatch" in res.error_message.lower()


def test_valid_synthetic_pdf_header_accepted():
    """Verify that valid PDF magic header passes validation."""
    valid_pdf_content = b"%PDF-1.7\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"
    res = FileValidator.validate_file("valid_policy.pdf", valid_pdf_content)
    assert res.is_valid
    assert res.sanitized_filename == "valid_policy.pdf"
    assert res.sha256_hash is not None


def test_audit_logger_records_change_history(in_memory_db: Session, sample_project: Project):
    """Verify that audit logger creates non-repudiable history entries in SQLite."""
    AuditLogger.log_action(
        db=in_memory_db,
        project_id=sample_project.id,
        action=AuditAction.ASSESSMENT_HUMAN_APPROVED,
        entity_type="GapAssessment",
        entity_id="test-assessment-uuid",
        performed_by="Lead Auditor Synthetic",
        previous_state={"status": "AI Draft", "compliance_score": 0.5},
        new_state={"status": "Human Approved", "compliance_score": 1.0},
        comment="Verified operational evidence in ticket system.",
    )

    history = AuditLogger.get_entity_history(
        db=in_memory_db,
        entity_type="GapAssessment",
        entity_id="test-assessment-uuid",
    )
    assert len(history) == 1
    assert history[0].action == AuditAction.ASSESSMENT_HUMAN_APPROVED.value
    assert history[0].performed_by == "Lead Auditor Synthetic"

