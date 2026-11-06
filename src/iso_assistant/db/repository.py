"""Repository layer providing clean CRUD abstraction for all compliance entities."""


from sqlalchemy.orm import Session

from iso_assistant.db.models import (
    Document,
    GapAssessment,
    ISOControl,
    Project,
    RiskItem,
)


class ProjectRepository:
    """Data access operations for projects and associated compliance records."""

    @staticmethod
    def get_or_create_default_project(db: Session) -> Project:
        """Retrieves active project or creates default initial workspace."""
        project = db.query(Project).first()
        if not project:
            project = Project(
                name="Default ISO 27001 Workspace",
                organization_name="Enterprise Organization",
                scope_description="Primary Information Security Management System (ISMS) scope.",
            )
            db.add(project)
            db.commit()
            db.refresh(project)
        return project

    @staticmethod
    def get_project(db: Session, project_id: str) -> Project | None:
        """Finds project by its primary key ID."""
        return db.query(Project).filter(Project.id == project_id).first()


class DocumentRepository:
    """Data access operations for uploaded documents and parsed contents."""

    @staticmethod
    def find_by_hash(db: Session, project_id: str, file_hash: str) -> Document | None:
        """Checks if a document with the identical cryptographic hash was already ingested."""
        return (
            db.query(Document)
            .filter(Document.project_id == project_id, Document.file_hash == file_hash)
            .first()
        )

    @staticmethod
    def save_document(db: Session, document: Document) -> Document:
        """Persists ingested document metadata and extracted text."""
        db.add(document)
        db.commit()
        db.refresh(document)
        return document

    @staticmethod
    def list_project_documents(db: Session, project_id: str) -> list[Document]:
        """Lists all uploaded documents for a project."""
        return db.query(Document).filter(Document.project_id == project_id).all()


class ControlRepository:
    """Data access operations for standard ISO 27001 control catalog."""

    @staticmethod
    def count_controls(db: Session) -> int:
        """Counts existing baseline controls in database."""
        return db.query(ISOControl).count()

    @staticmethod
    def bulk_insert_controls(db: Session, controls: list[ISOControl]) -> None:
        """Populates ISO 27001:2022 baseline controls in bulk."""
        db.bulk_save_objects(controls)
        db.commit()

    @staticmethod
    def get_all_controls(db: Session) -> list[ISOControl]:
        """Returns all reference controls ordered by ID."""
        return db.query(ISOControl).order_by(ISOControl.id).all()

    @staticmethod
    def get_control(db: Session, control_id: str) -> ISOControl | None:
        """Finds a specific control by its identifier (e.g. 'A.5.1')."""
        return db.query(ISOControl).filter(ISOControl.id == control_id).first()


class GapAssessmentRepository:
    """Data access operations for Gap Assessments."""

    @staticmethod
    def get_assessments_for_project(db: Session, project_id: str) -> list[GapAssessment]:
        """Retrieves all assessment records for a project."""
        return db.query(GapAssessment).filter(GapAssessment.project_id == project_id).all()

    @staticmethod
    def upsert_ai_assessment(db: Session, assessment: GapAssessment) -> GapAssessment:
        """Saves or updates an AI-generated assessment draft."""
        db.add(assessment)
        db.commit()
        db.refresh(assessment)
        return assessment


class RiskRepository:
    """Data access operations for Risk Register items."""

    @staticmethod
    def get_project_risks(db: Session, project_id: str) -> list[RiskItem]:
        """Retrieves all risk items for a project."""
        return db.query(RiskItem).filter(RiskItem.project_id == project_id).all()

    @staticmethod
    def save_risk(db: Session, risk_item: RiskItem) -> RiskItem:
        """Persists a new or updated risk item."""
        db.add(risk_item)
        db.commit()
        db.refresh(risk_item)
        return risk_item

