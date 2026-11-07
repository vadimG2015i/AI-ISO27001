"""Tests for clean database initialization, schema structure, and safety guarantees.

Covers:
1. Clean SQLite database initialization creates all tables and columns from models.py.
2. UniqueConstraint(project_id, file_hash) is created on a clean database and prevents duplicates.
3. init_db() is safe for repeated invocations on an existing database with current schema.
4. Outdated schema detection logs an informative warning without modifying/deleting data.
5. stored_path validation protects against path traversal and deletion outside upload_dir.
6. Orphan file cleanup on failed database persistence.
"""

import logging
from pathlib import Path
from typing import ClassVar
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker

from iso_assistant.db.connection import (
    Base,
    DatabaseSchemaError,
    _check_schema_compatibility,
)
from iso_assistant.db.models import Document, Project
from iso_assistant.services.document_service import DocumentService

# ---------------------------------------------------------------------------
# Clean DB Initialization & Schema Structure Tests
# ---------------------------------------------------------------------------

class TestDatabaseInitialization:
    """Verifies table creation and structure from models on a clean SQLite database."""

    EXPECTED_DOCUMENT_COLUMNS: ClassVar[set[str]] = {
        "id",
        "project_id",
        "filename",
        "stored_path",
        "file_type",
        "file_extension",
        "file_hash",
        "file_size_bytes",
        "extraction_status",
        "raw_text",
        "extracted_metadata",
        "processing_error",
        "uploaded_at",
    }

    def test_clean_db_creates_all_tables_and_columns(self):
        """Base.metadata.create_all creates all registered tables and expected columns on clean DB."""
        engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(bind=engine)

        inspector = inspect(engine)
        tables = set(inspector.get_table_names())
        assert "projects" in tables
        assert "documents" in tables
        assert "iso_controls" in tables
        assert "gap_assessments" in tables
        assert "risk_items" in tables
        assert "soa_items" in tables
        assert "audit_logs" in tables

        actual_cols = {c["name"] for c in inspector.get_columns("documents")}
        assert actual_cols == self.EXPECTED_DOCUMENT_COLUMNS

    def test_unique_constraint_created_on_clean_db(self):
        """UniqueConstraint('project_id', 'file_hash') is properly created on clean database."""
        engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(bind=engine)

        inspector = inspect(engine)
        unique_constraints = inspector.get_unique_constraints("documents")
        unique_col_sets = [set(uc["column_names"]) for uc in unique_constraints]

        # In SQLite, unique constraints are also reflected as unique indexes
        unique_indexes = [idx for idx in inspector.get_indexes("documents") if idx.get("unique")]
        unique_idx_col_sets = [set(idx["column_names"]) for idx in unique_indexes]

        target_cols = {"project_id", "file_hash"}
        assert target_cols in unique_col_sets or target_cols in unique_idx_col_sets, (
            "Unique constraint/index on (project_id, file_hash) was not created on clean DB"
        )

    def test_init_db_safe_to_call_repeatedly(self):
        """Calling init_db() or create_all multiple times on an existing valid database is completely safe."""
        engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(bind=engine)
        Base.metadata.create_all(bind=engine)  # repeated invocation

        inspector = inspect(engine)
        actual_cols = {c["name"] for c in inspector.get_columns("documents")}
        assert actual_cols == self.EXPECTED_DOCUMENT_COLUMNS

    def test_orm_operations_on_clean_db(self):
        """Ensures Document ORM operations succeed on clean DB initialized with create_all."""
        from datetime import UTC, datetime

        engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(bind=engine)

        TestSession = sessionmaker(bind=engine)
        session = TestSession()
        try:
            proj = Project(name="Test Org", organization_name="Compliance Lab")
            session.add(proj)
            session.commit()
            session.refresh(proj)

            doc = Document(
                project_id=proj.id,
                filename="policy.pdf",
                stored_path="/data/uploads/sample.pdf",
                file_type="PDF",
                file_extension=".pdf",
                file_hash="hash999",
                file_size_bytes=512,
                extraction_status="SUCCESS",
                raw_text="Extracted text",
                processing_error=None,
                uploaded_at=datetime.now(UTC),
            )
            session.add(doc)
            session.commit()

            loaded = session.query(Document).filter_by(file_hash="hash999").first()
            assert loaded is not None
            assert loaded.filename == "policy.pdf"
            assert loaded.stored_path == "/data/uploads/sample.pdf"
            assert loaded.extraction_status == "SUCCESS"
        finally:
            session.close()

    def test_outdated_schema_raises_error_without_modifying_db(self, caplog):
        """When an outdated table missing columns is encountered, raises DatabaseSchemaError and logs an error."""
        engine = create_engine("sqlite:///:memory:", echo=False)
        # Create an outdated table missing the 4 new Phase 1 columns
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE documents (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    file_hash TEXT NOT NULL,
                    file_size_bytes INTEGER NOT NULL,
                    raw_text TEXT,
                    extracted_metadata TEXT,
                    uploaded_at DATETIME
                )
            """))
            conn.execute(text(
                "INSERT INTO documents VALUES ('d1', 'p1', 'file.pdf', 'PDF', 'h1', 10, NULL, NULL, datetime('now'))"
            ))
            conn.commit()

        with caplog.at_level(logging.ERROR), pytest.raises(DatabaseSchemaError) as exc_info:
            _check_schema_compatibility(engine)

        # Verify informative error message
        assert "Database schema compatibility error" in str(exc_info.value)
        assert "recreate your local SQLite database manually" in str(exc_info.value)
        assert "extraction_status" in str(exc_info.value)

        # Verify existing data was untouched
        with engine.connect() as conn:
            rows = conn.execute(text("SELECT id, filename FROM documents")).fetchall()
        assert len(rows) == 1
        assert rows[0][0] == "d1"


# ---------------------------------------------------------------------------
# Fix 2: DB-level uniqueness constraint
# ---------------------------------------------------------------------------

class TestDatabaseLevelDeduplication:
    """Verifies UniqueConstraint(project_id, file_hash) prevents duplicate inserts."""

    def test_db_rejects_duplicate_hash_same_project(self, in_memory_db: Session):
        """Direct ORM insert with duplicate (project_id, file_hash) must raise IntegrityError."""
        from datetime import UTC, datetime

        from sqlalchemy.exc import IntegrityError

        project = Project(
            name="Dedup Test",
            organization_name="Test Corp",
        )
        in_memory_db.add(project)
        in_memory_db.commit()
        in_memory_db.refresh(project)

        common_kwargs = {
            "project_id": project.id,
            "file_type": "PDF",
            "file_hash": "samehash999",
            "file_size_bytes": 512,
            "extraction_status": "SUCCESS",
            "uploaded_at": datetime.now(UTC),
        }

        doc1 = Document(filename="policy_v1.pdf", **common_kwargs)
        in_memory_db.add(doc1)
        in_memory_db.commit()

        doc2 = Document(filename="policy_v2.pdf", **common_kwargs)
        in_memory_db.add(doc2)
        with pytest.raises(IntegrityError):
            in_memory_db.commit()

    def test_same_hash_allowed_across_different_projects(self, in_memory_db: Session):
        """Same file hash is permitted for different projects (not a duplicate)."""
        from datetime import UTC, datetime

        p1 = Project(name="Project A", organization_name="Org A")
        p2 = Project(name="Project B", organization_name="Org B")
        in_memory_db.add_all([p1, p2])
        in_memory_db.commit()
        in_memory_db.refresh(p1)
        in_memory_db.refresh(p2)

        common_kwargs = {
            "file_type": "PDF",
            "file_hash": "sharedhash",
            "file_size_bytes": 256,
            "extraction_status": "SUCCESS",
            "uploaded_at": datetime.now(UTC),
        }
        doc1 = Document(filename="policy.pdf", project_id=p1.id, **common_kwargs)
        doc2 = Document(filename="policy.pdf", project_id=p2.id, **common_kwargs)
        in_memory_db.add_all([doc1, doc2])
        in_memory_db.commit()  # Must NOT raise

        result = in_memory_db.query(Document).filter_by(file_hash="sharedhash").all()
        assert len(result) == 2


# ---------------------------------------------------------------------------
# Fix 3: stored_path validation on delete
# ---------------------------------------------------------------------------

class TestStoredPathValidation:
    """Verifies stored_path is validated against upload_dir before deletion."""

    def test_delete_refuses_path_outside_upload_dir(
        self, in_memory_db: Session, sample_project: Project, tmp_path: Path
    ):
        """delete_document must NOT delete a file whose stored_path is outside upload_dir."""
        from datetime import UTC, datetime

        # Create a sensitive file outside upload_dir
        sensitive_dir = tmp_path / "sensitive"
        sensitive_dir.mkdir()
        sensitive_file = sensitive_dir / "secret.txt"
        sensitive_file.write_text("top secret content")

        # Insert document record with tampered stored_path
        doc = Document(
            project_id=sample_project.id,
            filename="tampered.pdf",
            stored_path=str(sensitive_file),  # points outside upload_dir
            file_type="PDF",
            file_extension=".pdf",
            file_hash="tamperedhash",
            file_size_bytes=100,
            extraction_status="SUCCESS",
            uploaded_at=datetime.now(UTC),
        )
        in_memory_db.add(doc)
        in_memory_db.commit()
        in_memory_db.refresh(doc)

        # Use a different directory as upload_dir to ensure the path is outside it
        upload_dir = tmp_path / "uploads"
        upload_dir.mkdir()

        with patch("iso_assistant.services.document_service.settings") as mock_settings:
            mock_settings.upload_dir = upload_dir
            DocumentService.delete_document(
                db=in_memory_db,
                document_id=doc.id,
                delete_stored_file=True,
            )

        # The sensitive file must NOT have been deleted
        assert sensitive_file.exists(), (
            "delete_document must not delete files outside upload_dir"
        )

    def test_delete_removes_file_inside_upload_dir(
        self, in_memory_db: Session, sample_project: Project, tmp_path: Path
    ):
        """delete_document removes the file when stored_path is inside upload_dir."""
        from datetime import UTC, datetime

        upload_dir = tmp_path / "uploads"
        upload_dir.mkdir()
        stored_file = upload_dir / "abc123_policy.pdf"
        stored_file.write_bytes(b"%PDF-1.4 content")

        doc = Document(
            project_id=sample_project.id,
            filename="policy.pdf",
            stored_path=str(stored_file),
            file_type="PDF",
            file_extension=".pdf",
            file_hash="goodhash",
            file_size_bytes=16,
            extraction_status="SUCCESS",
            uploaded_at=datetime.now(UTC),
        )
        in_memory_db.add(doc)
        in_memory_db.commit()
        in_memory_db.refresh(doc)

        with patch("iso_assistant.services.document_service.settings") as mock_settings:
            mock_settings.upload_dir = upload_dir
            DocumentService.delete_document(
                db=in_memory_db,
                document_id=doc.id,
                delete_stored_file=True,
            )

        assert not stored_file.exists(), "File inside upload_dir should have been deleted"

    def test_delete_relative_path_handled_safely(
        self, in_memory_db: Session, sample_project: Project, tmp_path: Path
    ):
        """Relative stored_path is safely resolved against upload_dir and deleted if inside."""
        from datetime import UTC, datetime

        upload_dir = tmp_path / "uploads"
        upload_dir.mkdir()
        stored_file = upload_dir / "relative_policy.pdf"
        stored_file.write_bytes(b"%PDF-1.4 content")

        doc = Document(
            project_id=sample_project.id,
            filename="relative_policy.pdf",
            stored_path="relative_policy.pdf",  # relative path
            file_type="PDF",
            file_extension=".pdf",
            file_hash="relhash",
            file_size_bytes=16,
            extraction_status="SUCCESS",
            uploaded_at=datetime.now(UTC),
        )
        in_memory_db.add(doc)
        in_memory_db.commit()
        in_memory_db.refresh(doc)

        with patch("iso_assistant.services.document_service.settings") as mock_settings:
            mock_settings.upload_dir = upload_dir
            DocumentService.delete_document(
                db=in_memory_db,
                document_id=doc.id,
                delete_stored_file=True,
            )

        assert not stored_file.exists(), "Relative file inside upload_dir should have been deleted"

    def test_delete_symlink_mocked_logic(
        self, in_memory_db: Session, sample_project: Project, tmp_path: Path
    ):
        """Cross-platform verification of symlink handling logic using mocked paths."""
        from datetime import UTC, datetime

        upload_dir = tmp_path / "uploads"
        upload_dir.mkdir()
        outside_file = tmp_path / "outside_secret.txt"
        outside_file.write_text("secret")

        # 1. Symlink pointing outside upload_dir
        doc_outside = Document(
            project_id=sample_project.id,
            filename="sym_outside.pdf",
            stored_path=str(upload_dir / "sym_outside.pdf"),
            file_type="PDF",
            file_extension=".pdf",
            file_hash="hash_out",
            file_size_bytes=10,
            extraction_status="SUCCESS",
            uploaded_at=datetime.now(UTC),
        )
        in_memory_db.add(doc_outside)
        in_memory_db.commit()

        orig_resolve = Path.resolve

        def resolve_outside(p):
            if p.name == "sym_outside.pdf":
                return outside_file.resolve()
            return orig_resolve(p)

        with patch("iso_assistant.services.document_service.settings") as mock_settings, \
             patch.object(Path, "is_symlink", autospec=True, side_effect=lambda p: p.name == "sym_outside.pdf"), \
             patch.object(Path, "resolve", resolve_outside), \
             patch.object(Path, "unlink") as mock_unlink:
            mock_settings.upload_dir = upload_dir
            DocumentService.delete_document(in_memory_db, doc_outside.id, delete_stored_file=True)
            assert not mock_unlink.called, "Unlink must NOT be called for symlink pointing outside upload_dir"

        # 2. Symlink pointing inside upload_dir
        inside_target = upload_dir / "real_inside.pdf"
        inside_target.write_bytes(b"data")

        doc_inside = Document(
            project_id=sample_project.id,
            filename="sym_inside.pdf",
            stored_path=str(upload_dir / "sym_inside.pdf"),
            file_type="PDF",
            file_extension=".pdf",
            file_hash="hash_in",
            file_size_bytes=10,
            extraction_status="SUCCESS",
            uploaded_at=datetime.now(UTC),
        )
        in_memory_db.add(doc_inside)
        in_memory_db.commit()

        def resolve_inside(p):
            if p.name == "sym_inside.pdf":
                return inside_target.resolve()
            return orig_resolve(p)

        with patch("iso_assistant.services.document_service.settings") as mock_settings, \
             patch.object(Path, "is_symlink", autospec=True, side_effect=lambda p: p.name == "sym_inside.pdf"), \
             patch.object(Path, "resolve", resolve_inside), \
             patch.object(Path, "unlink") as mock_unlink:
            mock_settings.upload_dir = upload_dir
            DocumentService.delete_document(in_memory_db, doc_inside.id, delete_stored_file=True)
            assert mock_unlink.called, "Unlink MUST be called for symlink pointing inside upload_dir"

    def test_delete_symlink_pointing_outside_refused(
        self, in_memory_db: Session, sample_project: Project, tmp_path: Path
    ):
        """Symlink in upload_dir pointing outside upload_dir must NOT be followed or deleted."""
        import os
        from datetime import UTC, datetime

        upload_dir = tmp_path / "uploads"
        upload_dir.mkdir()
        outside_dir = tmp_path / "outside"
        outside_dir.mkdir()
        target_file = outside_dir / "target_secret.txt"
        target_file.write_text("critical secret")

        symlink_file = upload_dir / "link_to_secret.pdf"
        try:
            os.symlink(target_file, symlink_file)
        except (OSError, NotImplementedError):
            pytest.skip("Symlink creation not supported in this environment/privilege level")

        doc = Document(
            project_id=sample_project.id,
            filename="link_to_secret.pdf",
            stored_path=str(symlink_file),
            file_type="PDF",
            file_extension=".pdf",
            file_hash="linkhash",
            file_size_bytes=10,
            extraction_status="SUCCESS",
            uploaded_at=datetime.now(UTC),
        )
        in_memory_db.add(doc)
        in_memory_db.commit()

        with patch("iso_assistant.services.document_service.settings") as mock_settings:
            mock_settings.upload_dir = upload_dir
            DocumentService.delete_document(
                db=in_memory_db,
                document_id=doc.id,
                delete_stored_file=True,
            )

        assert target_file.exists(), "Target file outside upload_dir must NEVER be deleted"
        assert symlink_file.exists(), "Symlink pointing outside upload_dir must NOT be deleted"

    def test_delete_symlink_inside_upload_dir_deletes_link_not_target(
        self, in_memory_db: Session, sample_project: Project, tmp_path: Path
    ):
        """Symlink inside upload_dir pointing inside upload_dir unlinks the symlink, preserving the target."""
        import os
        from datetime import UTC, datetime

        upload_dir = tmp_path / "uploads"
        upload_dir.mkdir()
        target_file = upload_dir / "original_file.pdf"
        target_file.write_bytes(b"%PDF-1.4 real data")

        symlink_file = upload_dir / "alias_link.pdf"
        try:
            os.symlink(target_file, symlink_file)
        except (OSError, NotImplementedError):
            pytest.skip("Symlink creation not supported in this environment/privilege level")

        doc = Document(
            project_id=sample_project.id,
            filename="alias_link.pdf",
            stored_path=str(symlink_file),
            file_type="PDF",
            file_extension=".pdf",
            file_hash="aliashash",
            file_size_bytes=10,
            extraction_status="SUCCESS",
            uploaded_at=datetime.now(UTC),
        )
        in_memory_db.add(doc)
        in_memory_db.commit()

        with patch("iso_assistant.services.document_service.settings") as mock_settings:
            mock_settings.upload_dir = upload_dir
            DocumentService.delete_document(
                db=in_memory_db,
                document_id=doc.id,
                delete_stored_file=True,
            )

        assert not symlink_file.exists(), "Symlink itself should be unlinked"
        assert target_file.exists(), "Target file must be preserved and NOT deleted"


# ---------------------------------------------------------------------------
# Fix 4: Orphan file cleanup when DB save fails
# ---------------------------------------------------------------------------

class TestOrphanFileCleanup:
    """Verifies that files are cleaned up when DB persistence fails."""

    def test_orphan_file_removed_on_db_failure(
        self, in_memory_db: Session, sample_project: Project, tmp_path: Path
    ):
        """When save_document() raises, the uploaded file must be deleted from disk."""
        import io

        from reportlab.pdfgen import canvas

        buf = io.BytesIO()
        c = canvas.Canvas(buf)
        c.drawString(72, 750, "Test policy content")
        c.showPage()
        c.save()
        pdf_bytes = buf.getvalue()

        stored_files_before = list(tmp_path.glob("*.pdf"))

        # Patch save_document to simulate a DB failure after file is written to disk
        with patch(
            "iso_assistant.services.document_service.DocumentRepository.save_document",
            side_effect=Exception("Simulated DB failure: disk full"),
        ), pytest.raises(Exception, match="Failed to persist document to database"):
            DocumentService.ingest_document(
                db=in_memory_db,
                project_id=sample_project.id,
                filename="orphan_test.pdf",
                content=pdf_bytes,
                upload_dir=tmp_path,
            )

        # No new PDF files should remain on disk
        stored_files_after = list(tmp_path.glob("*.pdf"))
        assert stored_files_after == stored_files_before, (
            f"Orphan file(s) left on disk after DB failure: "
            f"{[f.name for f in stored_files_after]}"
        )

        # No document record in DB either
        docs = in_memory_db.query(Document).filter_by(project_id=sample_project.id).all()
        assert len(docs) == 0, "No DB record should exist after failed persistence"

    def test_name_conflict_prevents_overwriting_preexisting_file(
        self, in_memory_db: Session, sample_project: Project, tmp_path: Path
    ):
        """If a file with the destination name already exists on disk, it must not be overwritten or deleted."""
        import io

        from reportlab.pdfgen import canvas

        from iso_assistant.security.file_validator import DocumentValidationError, FileValidator

        buf = io.BytesIO()
        c = canvas.Canvas(buf)
        c.drawString(72, 750, "Incoming content")
        c.showPage()
        c.save()
        pdf_bytes = buf.getvalue()

        # Compute hash and destination name
        file_hash = FileValidator.compute_sha256(pdf_bytes)
        safe_name = FileValidator.generate_safe_storage_name("conflict.pdf", file_hash)
        preexisting_file = tmp_path / safe_name
        original_data = b"Pre-existing precious file content that must NOT be overwritten"
        preexisting_file.write_bytes(original_data)

        # Ingestion must fail due to FileExists collision
        with pytest.raises(DocumentValidationError, match="Storage collision"):
            DocumentService.ingest_document(
                db=in_memory_db,
                project_id=sample_project.id,
                filename="conflict.pdf",
                content=pdf_bytes,
                upload_dir=tmp_path,
            )

        # The pre-existing file must remain completely intact
        assert preexisting_file.exists()
        assert preexisting_file.read_bytes() == original_data
