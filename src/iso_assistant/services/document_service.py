"""Document ingestion and lifecycle management service."""

import json
from pathlib import Path

from sqlalchemy.orm import Session

from iso_assistant.config import settings
from iso_assistant.constants import AuditAction
from iso_assistant.db.models import Document
from iso_assistant.db.repository import DocumentRepository
from iso_assistant.extractors.base import DocumentExtractionError, ExtractedDocument
from iso_assistant.extractors.factory import ExtractorFactory
from iso_assistant.security.audit_logger import AuditLogger
from iso_assistant.security.file_validator import (
    DocumentValidationError,
    DuplicateDocumentError,
    FileValidator,
)
from iso_assistant.utils.logger import get_logger

logger = get_logger(__name__)


class DocumentService:
    """Orchestrates secure file validation, storage, parsing, and database persistence."""

    @classmethod
    def ingest_document(
        cls,
        db: Session,
        project_id: str,
        filename: str,
        content: bytes,
        uploaded_by: str = "Compliance Officer",
        upload_dir: Path | None = None,
        raise_on_extraction_error: bool = False,
    ) -> Document:
        """Processes an uploaded compliance artifact through the ingestion pipeline.

        Pipeline Stages:
        1. Security validation (size, extension, MIME magic signature, path sanitization).
        2. Deduplication check via SHA-256 hash.
        3. Secure file storage in designated upload directory (outside source directories).
        4. Document text and table extraction.
        5. Database persistence with extraction status and metadata.
        6. Audit trail logging.

        Args:
            db: Active SQLAlchemy database session.
            project_id: ID of the compliance project workspace.
            filename: Original user-provided filename.
            content: Raw binary content of the file.
            uploaded_by: Name or role of the user uploading the file.
            upload_dir: Optional custom storage directory (defaults to settings.upload_dir).
            raise_on_extraction_error: If True, raises DocumentExtractionError on parse failure;
                                       if False, persists document with extraction_status='FAILED'.

        Returns:
            Persisted Document entity.

        Raises:
            DocumentValidationError: If security or format checks fail.
            DuplicateDocumentError: If an identical document has already been ingested.
            DocumentExtractionError: If extraction fails and raise_on_extraction_error is True.
        """
        # 1. Security validation
        val_result = FileValidator.validate_file(filename, content)
        if not val_result.is_valid:
            logger.warning("File validation rejected '%s': %s", filename, val_result.error_message)
            raise DocumentValidationError(val_result.error_message or "File validation failed.")

        # 2. Deduplication check via SHA-256
        existing = DocumentRepository.find_by_hash(db, project_id, val_result.sha256_hash)
        if existing:
            logger.info("Duplicate file detected for project %s (hash: %s)", project_id, val_result.sha256_hash)
            raise DuplicateDocumentError(
                f"Document with identical content already exists: '{existing.filename}' (ID: {existing.id})."
            )

        # 3. Secure file storage
        target_dir = Path(upload_dir or settings.upload_dir).resolve()

        # Guard: Never store inside source code directories
        src_dir = (Path(__file__).resolve().parent.parent).resolve()
        if target_dir == src_dir or src_dir in target_dir.parents:
            raise DocumentValidationError("Upload directory cannot be located inside source code directories.")

        target_dir.mkdir(parents=True, exist_ok=True)
        safe_name = FileValidator.generate_safe_storage_name(
            val_result.sanitized_filename, val_result.sha256_hash
        )
        stored_file_path = (target_dir / safe_name).resolve()

        # Guard against path traversal within safe_name
        if not stored_file_path.is_relative_to(target_dir):
            raise DocumentValidationError("Generated storage path escapes upload directory.")

        # Atomic creation to guarantee unique file creation and prevent overwriting existing files
        file_created_by_current_op = False
        try:
            with open(stored_file_path, "xb") as f:
                f.write(content)
            file_created_by_current_op = True
        except FileExistsError as exists_err:
            logger.error("Storage collision: file '%s' already exists in upload directory.", stored_file_path)
            raise DocumentValidationError(
                f"Storage collision: file already exists in destination: {stored_file_path.name}"
            ) from exists_err
        except OSError as io_err:
            logger.error("Failed to write document to storage path '%s': %s", stored_file_path, io_err)
            raise DocumentValidationError(f"Failed to securely store uploaded file: {io_err}") from io_err

        # 4. Text extraction
        extracted_doc: ExtractedDocument | None = None
        extraction_status = "SUCCESS"
        processing_error: str | None = None
        raw_text: str = ""
        metadata: dict = {
            "sanitized_filename": val_result.sanitized_filename,
            "detected_mime_type": val_result.detected_mime_type,
        }

        try:
            extractor = ExtractorFactory.get_extractor(val_result.sanitized_filename)
            extracted_doc = extractor.extract(content, val_result.sanitized_filename)
            raw_text = extracted_doc.raw_text
            extraction_status = extracted_doc.extraction_status
            metadata.update(extracted_doc.metadata)
            metadata["page_count"] = extracted_doc.page_count
            metadata["sheet_count"] = extracted_doc.sheet_count
            metadata["table_count"] = extracted_doc.table_count
            metadata["character_count"] = extracted_doc.character_count
            metadata["word_count"] = extracted_doc.estimated_word_count
            if extracted_doc.warnings:
                metadata["warnings"] = extracted_doc.warnings
        except DocumentExtractionError as extract_err:
            logger.warning("Extraction error for '%s': %s", val_result.sanitized_filename, extract_err)
            if raise_on_extraction_error:
                # Clean up stored file on abort (only if created by current operation)
                if file_created_by_current_op and stored_file_path.exists():
                    stored_file_path.unlink(missing_ok=True)
                raise
            extraction_status = "FAILED"
            processing_error = str(extract_err)
            metadata["extraction_error"] = str(extract_err)
        except Exception as unexp_err:
            logger.error("Unexpected error extracting '%s': %s", val_result.sanitized_filename, unexp_err)
            if raise_on_extraction_error:
                if file_created_by_current_op and stored_file_path.exists():
                    stored_file_path.unlink(missing_ok=True)
                raise DocumentExtractionError(f"Unexpected extraction failure: {unexp_err}") from unexp_err
            extraction_status = "FAILED"
            processing_error = f"Unexpected extraction failure: {unexp_err}"
            metadata["extraction_error"] = processing_error

        # 5. Database persistence
        doc_entity = Document(
            project_id=project_id,
            filename=val_result.sanitized_filename,
            stored_path=str(stored_file_path),
            file_type=(extracted_doc.file_type if extracted_doc else val_result.file_extension.lstrip(".").upper()),
            file_extension=val_result.file_extension,
            file_hash=val_result.sha256_hash,
            file_size_bytes=val_result.file_size_bytes,
            extraction_status=extraction_status,
            raw_text=raw_text if extraction_status != "FAILED" else None,
            extracted_metadata=json.dumps(metadata),
            processing_error=processing_error,
        )

        try:
            persisted_doc = DocumentRepository.save_document(db, doc_entity)
        except Exception as db_err:
            # Fix 4: Cleanup orphan file when DB persistence fails.
            # Only cleans up the file created by the current operation to protect pre-existing files.
            logger.error(
                "Database persistence failed for '%s': %s. Removing orphan file.",
                val_result.sanitized_filename,
                db_err,
            )
            if file_created_by_current_op and stored_file_path.exists():
                stored_file_path.unlink(missing_ok=True)
            raise DocumentValidationError(
                f"Failed to persist document to database: {db_err}"
            ) from db_err

        # 6. Audit trail logging
        AuditLogger.log_action(
            db=db,
            project_id=project_id,
            action=AuditAction.DOCUMENT_UPLOAD,
            entity_type="Document",
            entity_id=persisted_doc.id,
            performed_by=uploaded_by,
            new_state={
                "filename": persisted_doc.filename,
                "file_hash": persisted_doc.file_hash,
                "file_size": persisted_doc.file_size_bytes,
                "status": persisted_doc.extraction_status,
            },
            comment=f"Ingested document '{persisted_doc.filename}' ({persisted_doc.file_type}).",
        )

        logger.info(
            "Successfully ingested document '%s' (ID: %s, Status: %s)",
            persisted_doc.filename,
            persisted_doc.id,
            persisted_doc.extraction_status,
        )
        return persisted_doc

    @classmethod
    def get_document(cls, db: Session, document_id: str) -> Document | None:
        """Retrieves a document record by ID."""
        return DocumentRepository.find_by_id(db, document_id)

    @classmethod
    def list_documents(cls, db: Session, project_id: str) -> list[Document]:
        """Returns all ingested documents for a specific compliance workspace."""
        return DocumentRepository.list_project_documents(db, project_id)

    @classmethod
    def delete_document(
        cls,
        db: Session,
        document_id: str,
        deleted_by: str = "Compliance Officer",
        delete_stored_file: bool = True,
    ) -> bool:
        """Deletes a document from the database and optionally removes the physical file."""
        doc = DocumentRepository.find_by_id(db, document_id)
        if not doc:
            return False

        project_id = doc.project_id
        stored_path = doc.stored_path
        filename = doc.filename

        # Remove physical file if requested
        if delete_stored_file and stored_path:
            raw_path = Path(stored_path)
            allowed_base = Path(settings.upload_dir).resolve()

            # Ensure relative paths are treated relative to allowed_base
            candidate = (allowed_base / raw_path) if not raw_path.is_absolute() else raw_path

            # Strict security checks:
            # 1. Do NOT delete directories or root paths.
            # 2. Check if candidate path is a symlink.
            #    - If it is a symlink, never follow it to delete the target.
            #    - Reject deletion if the symlink or its target escapes allowed_base.
            # 3. For regular files, candidate must resolve strictly inside allowed_base.
            try:
                # Do not follow symlinks when checking existence
                if candidate.is_symlink():
                    resolved_target = candidate.resolve()
                    # Check if the symlink file itself is within upload_dir
                    parent_resolved = candidate.parent.resolve()
                    if not (parent_resolved == allowed_base or parent_resolved.is_relative_to(allowed_base)):
                        logger.warning("Refused to delete symlink outside upload_dir: %s", candidate)
                    elif not (resolved_target == allowed_base or resolved_target.is_relative_to(allowed_base)):
                        logger.warning(
                            "Refused to delete symlink pointing outside upload_dir: %s -> %s",
                            candidate,
                            resolved_target,
                        )
                    else:
                        # Safely unlink the symlink itself (not the target!)
                        candidate.unlink(missing_ok=True)
                elif candidate.is_dir():
                    logger.warning("Refused to delete directory path: %s", candidate)
                elif candidate.exists():
                    resolved_file = candidate.resolve()
                    if resolved_file == allowed_base or not resolved_file.is_relative_to(allowed_base):
                        logger.warning("Refused to delete file outside upload_dir: %s", candidate)
                    else:
                        candidate.unlink(missing_ok=True)
            except OSError as err:
                logger.error("Error inspecting/deleting stored file '%s': %s", candidate, err)

        success = DocumentRepository.delete_document(db, document_id)
        if success:
            AuditLogger.log_action(
                db=db,
                project_id=project_id,
                action=AuditAction.DOCUMENT_DELETE,
                entity_type="Document",
                entity_id=document_id,
                performed_by=deleted_by,
                previous_state={"filename": filename},
                comment=f"Deleted document '{filename}'.",
            )
        return success
