"""SQLAlchemy 2.0 declarative database entities for ISO 27001 compliance management."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from iso_assistant.db.connection import Base


def generate_uuid() -> str:
    """Generates unique primary key identifier."""
    return str(uuid.uuid4())


class Project(Base):
    """Represents an organization or distinct compliance audit engagement."""

    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(128), nullable=False)
    organization_name = Column(String(128), nullable=False)
    scope_description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    # Relationships
    documents = relationship("Document", back_populates="project", cascade="all, delete-orphan")
    gap_assessments = relationship("GapAssessment", back_populates="project", cascade="all, delete-orphan")
    risk_items = relationship("RiskItem", back_populates="project", cascade="all, delete-orphan")
    soa_items = relationship("StatementOfApplicabilityItem", back_populates="project", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="project", cascade="all, delete-orphan")


class Document(Base):
    """Metadata and extracted content of uploaded compliance documents."""

    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(16), nullable=False)  # PDF, DOCX, XLSX
    file_hash = Column(String(64), nullable=False, index=True)  # SHA-256
    file_size_bytes = Column(Integer, nullable=False)
    raw_text = Column(Text, nullable=True)
    extracted_metadata = Column(Text, nullable=True)  # JSON-serialized metadata
    uploaded_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)

    project = relationship("Project", back_populates="documents")


class ISOControl(Base):
    """Structural baseline reference for ISO/IEC 27001:2022 clauses and Annex A controls.

    Contains non-copyrighted structural descriptors, identifiers, and public themes.
    """

    __tablename__ = "iso_controls"

    id = Column(String(32), primary_key=True)  # e.g., "A.5.1", "Clause.4.1"
    category = Column(String(32), nullable=False)  # "Clause" or "Annex A"
    theme = Column(String(64), nullable=False)  # "Organizational", "People", etc.
    title = Column(String(255), nullable=False)
    summary = Column(Text, nullable=True)
    guidance = Column(Text, nullable=True)

    assessments = relationship("GapAssessment", back_populates="control")
    soa_entries = relationship("StatementOfApplicabilityItem", back_populates="control")


class GapAssessment(Base):
    """ISO 27001 gap assessment record with strict separation between AI draft and Human approved states."""

    __tablename__ = "gap_assessments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    control_id = Column(String(32), ForeignKey("iso_controls.id"), nullable=False)

    # Lifecycle Review Status
    review_status = Column(String(32), nullable=False, default="AI Draft")  # ReviewStatus enum value

    # AI Draft Assessment Fields
    ai_status = Column(String(32), nullable=True)  # Compliant, Partially Compliant, Non-Compliant, Not Applicable
    ai_compliance_score = Column(Float, nullable=True)  # 0.0 to 1.0
    ai_evidence_found = Column(Text, nullable=True)
    ai_identified_gaps = Column(Text, nullable=True)
    ai_remediation_plan = Column(Text, nullable=True)
    ai_confidence_score = Column(Float, nullable=True)
    ai_model_name = Column(String(64), nullable=True)
    ai_assessed_at = Column(DateTime, nullable=True)

    # Human Auditor Overrides & Approval
    human_status = Column(String(32), nullable=True)
    human_compliance_score = Column(Float, nullable=True)
    human_notes = Column(Text, nullable=True)
    approved_by = Column(String(128), nullable=True)
    approved_at = Column(DateTime, nullable=True)

    # Relationships
    project = relationship("Project", back_populates="gap_assessments")
    control = relationship("ISOControl", back_populates="assessments")


class RiskItem(Base):
    """Information security risk register item aligned with ISO/IEC 27005."""

    __tablename__ = "risk_items"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    risk_title = Column(String(255), nullable=False)
    asset_or_process = Column(String(255), nullable=False)
    threat = Column(Text, nullable=False)
    vulnerability = Column(Text, nullable=False)
    impacted_cia = Column(String(64), nullable=False)  # CIAProperty

    # Inherent Risk (1-5 scale)
    inherent_likelihood = Column(Integer, CheckConstraint("inherent_likelihood BETWEEN 1 AND 5"), nullable=False)
    inherent_impact = Column(Integer, CheckConstraint("inherent_impact BETWEEN 1 AND 5"), nullable=False)
    inherent_risk_score = Column(Integer, nullable=False)  # likelihood * impact
    inherent_risk_level = Column(String(32), nullable=False)

    # Treatment & Mitigations
    treatment_strategy = Column(String(32), nullable=False)  # Mitigate, Avoid, Transfer, Accept
    treatment_details = Column(Text, nullable=True)
    mapped_controls = Column(Text, nullable=True)  # JSON-encoded array of Annex A control IDs

    # Residual Risk (1-5 scale)
    residual_likelihood = Column(Integer, CheckConstraint("residual_likelihood BETWEEN 1 AND 5"), nullable=True)
    residual_impact = Column(Integer, CheckConstraint("residual_impact BETWEEN 1 AND 5"), nullable=True)
    residual_risk_score = Column(Integer, nullable=True)
    residual_risk_level = Column(String(32), nullable=True)

    # Governance
    risk_owner = Column(String(128), nullable=True)
    status = Column(String(32), nullable=False, default="Open")  # Open, In Progress, Mitigated, Accepted
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    project = relationship("Project", back_populates="risk_items")


class StatementOfApplicabilityItem(Base):
    """Statement of Applicability (SoA) entry for ISO 27001:2022 Annex A controls."""

    __tablename__ = "soa_items"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    control_id = Column(String(32), ForeignKey("iso_controls.id"), nullable=False)
    is_applicable = Column(Boolean, nullable=False, default=True)
    justification = Column(Text, nullable=False)  # Required justification for inclusion or exclusion
    implementation_status = Column(String(64), nullable=False, default="Planned")
    responsible_role = Column(String(128), nullable=True)
    target_date = Column(String(32), nullable=True)
    auditor_verified = Column(Boolean, nullable=False, default=False)
    verified_by = Column(String(128), nullable=True)
    verified_at = Column(DateTime, nullable=True)

    project = relationship("Project", back_populates="soa_items")
    control = relationship("ISOControl", back_populates="soa_entries")


class AuditLog(Base):
    """Tamper-evident audit trail capturing compliance modifications and approvals."""

    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    action = Column(String(64), nullable=False)  # AuditAction enum
    entity_type = Column(String(64), nullable=False)  # Document, GapAssessment, RiskItem, SoA
    entity_id = Column(String(36), nullable=False)
    performed_by = Column(String(128), nullable=False)
    previous_state = Column(Text, nullable=True)  # JSON representation
    new_state = Column(Text, nullable=True)       # JSON representation
    comment = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False, index=True)

    project = relationship("Project", back_populates="audit_logs")

