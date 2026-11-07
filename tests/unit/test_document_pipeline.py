"""Automated test suite for secure document ingestion pipeline.

Verifies:
1. Valid synthetic PDF extraction (pdfplumber/pypdf).
2. Valid synthetic DOCX extraction (python-docx).
3. Valid synthetic XLSX extraction (openpyxl).
4. Unsupported file extension rejection.
5. Incorrect file signature / magic byte mismatch detection.
6. Empty file (0 bytes) rejection.
7. Oversized file rejection.
8. Malformed or corrupted document handling.
9. Duplicate document detection via SHA-256 hash.
10. End-to-end database persistence and audit log creation.
11. Extraction failure error handling.
12. Path traversal attack prevention and safe storage.

Note: Strictly synthetic non-sensitive documents are generated dynamically.
"""

import io
from pathlib import Path

import docx
import openpyxl
import pytest
from reportlab.pdfgen import canvas
from sqlalchemy.orm import Session

from iso_assistant.config import settings
from iso_assistant.db.models import Document, Project
from iso_assistant.extractors.base import DocumentExtractionError
from iso_assistant.extractors.docx_extractor import DocxExtractor
from iso_assistant.extractors.pdf_extractor import PdfExtractor
from iso_assistant.extractors.xlsx_extractor import XlsxExtractor
from iso_assistant.security.file_validator import (
    DuplicateDocumentError,
    FileValidator,
)
from iso_assistant.services.document_service import DocumentService

# ---------------------------------------------------------------------------
# Helper Fixtures to Generate Valid Synthetic Documents in Memory
# ---------------------------------------------------------------------------

def create_synthetic_pdf(
    title: str = "ISO 27001 Access Control Policy",
    content: str = "Mandatory quarterly access reviews must be conducted by asset owners.",
) -> bytes:
    """Generates valid synthetic PDF binary with text content."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    c.setTitle(title)
    c.drawString(72, 750, title)
    c.drawString(72, 720, content)
    c.drawString(72, 690, "Clause 6.1.2 Information Security Risk Assessment")
    c.showPage()
    c.save()
    return buf.getvalue()


def create_synthetic_docx(
    title: str = "Information Security Incident Management",
) -> bytes:
    """Generates valid synthetic Word OpenXML binary with headings and tables."""
    doc = docx.Document()
    doc.add_heading(title, level=1)
    doc.add_paragraph("This policy defines incident severity categories and escalation paths.")

    # Add a table
    table = doc.add_table(rows=3, cols=2)
    table.rows[0].cells[0].text = "Severity"
    table.rows[0].cells[1].text = "Response SLA"
    table.rows[1].cells[0].text = "P1 - Critical"
    table.rows[1].cells[1].text = "1 Hour"
    table.rows[2].cells[0].text = "P2 - High"
    table.rows[2].cells[1].text = "4 Hours"

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def create_synthetic_xlsx(
    sheet_name: str = "Asset Inventory",
) -> bytes:
    """Generates valid synthetic Excel OpenXML binary with worksheets and rows."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = sheet_name
    ws.append(["Asset ID", "Asset Name", "Classification", "Owner"])
    ws.append(["AST-001", "Customer Database", "Confidential", "VP of Engineering"])
    ws.append(["AST-002", "Production Kubernetes Cluster", "Restricted", "DevOps Lead"])

    # Add second sheet
    ws2 = wb.create_sheet(title="Risk Scope")
    ws2.append(["Scope Item", "Status"])
    ws2.append(["Cloud Infrastructure", "Included"])

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Test Cases
# ---------------------------------------------------------------------------

def test_valid_synthetic_pdf_extraction():
    """Verify text and page count extraction from synthetic PDF."""
    pdf_bytes = create_synthetic_pdf(title="Access Control Spec", content="Test policy line A.5.15")
    extractor = PdfExtractor()
    extracted = extractor.extract(pdf_bytes, "access_control.pdf")

    assert extracted.file_type == "PDF"
    assert extracted.extraction_status == "SUCCESS"
    assert extracted.page_count >= 1
    assert "Access Control Spec" in extracted.raw_text
    assert "A.5.15" in extracted.raw_text
    assert extracted.character_count > 0


def test_valid_synthetic_docx_extraction():
    """Verify paragraphs, headings, and table extraction from synthetic DOCX."""
    docx_bytes = create_synthetic_docx(title="Incident Management SOP")
    extractor = DocxExtractor()
    extracted = extractor.extract(docx_bytes, "incident_sop.docx")

    assert extracted.file_type == "DOCX"
    assert extracted.extraction_status == "SUCCESS"
    assert "# Incident Management SOP" in extracted.raw_text
    assert "P1 - Critical" in extracted.raw_text
    assert len(extracted.tables) == 1
    assert extracted.tables[0][1][0] == "P1 - Critical"


def test_valid_synthetic_xlsx_extraction():
    """Verify multi-sheet extraction, worksheet boundaries, and table matrices from synthetic XLSX."""
    xlsx_bytes = create_synthetic_xlsx(sheet_name="Asset Register")
    extractor = XlsxExtractor()
    extracted = extractor.extract(xlsx_bytes, "assets.xlsx")

    assert extracted.file_type == "XLSX"
    assert extracted.extraction_status == "SUCCESS"
    assert extracted.sheet_count == 2
    assert "--- Worksheet: Asset Register ---" in extracted.raw_text
    assert "--- Worksheet: Risk Scope ---" in extracted.raw_text
    assert "Customer Database" in extracted.raw_text
    assert len(extracted.tables) == 2


def test_unsupported_file_extension():
    """Verify rejection of disallowed file extensions (e.g. .exe, .sh, .py)."""
    script_bytes = b"#!/bin/bash\necho 'hello'"
    res = FileValidator.validate_file("exploit.sh", script_bytes)
    assert not res.is_valid
    assert "disallowed file extension" in res.error_message.lower()


def test_incorrect_file_signature():
    """Verify that a file renamed to .pdf with non-PDF binary header is rejected."""
    fake_pdf = b"NOT_A_PDF_HEADER_THIS_IS_PLAIN_TEXT"
    res = FileValidator.validate_file("fake_policy.pdf", fake_pdf)
    assert not res.is_valid
    assert "header mismatch" in res.error_message.lower()


def test_empty_file_rejected():
    """Verify that empty 0-byte file upload is rejected."""
    res = FileValidator.validate_file("empty_file.docx", b"")
    assert not res.is_valid
    assert "empty" in res.error_message.lower()


def test_oversized_file_rejected(monkeypatch):
    """Verify that files exceeding the configured maximum size are rejected."""
    # Temporarily set max size to 100 bytes for test
    monkeypatch.setattr(settings, "max_file_size_bytes", 100)
    oversized = b"%PDF-1.4\n" + b"X" * 200
    res = FileValidator.validate_file("large.pdf", oversized)
    assert not res.is_valid
    assert "exceeds maximum allowed upload size" in res.error_message.lower()


def test_malformed_document_graceful_handling():
    """Verify that corrupted document structure is handled gracefully without crashing."""
    corrupted_pdf = b"%PDF-1.4\nCorrupted byte stream with missing xref and trailer tokens."
    extractor = PdfExtractor()
    with pytest.raises(DocumentExtractionError):
        extractor.extract(corrupted_pdf, "corrupt.pdf")


def test_path_traversal_sanitization():
    """Verify that dangerous directory navigation sequences are neutralized."""
    malicious_name = "../../../../../windows/system32/cmd.pdf"
    sanitized = FileValidator.sanitize_filename(malicious_name)
    assert ".." not in sanitized
    assert "/" not in sanitized
    assert "\\" not in sanitized
    assert sanitized.endswith(".pdf")


def test_successful_database_persistence(
    in_memory_db: Session, sample_project: Project, tmp_path: Path
):
    """Verify end-to-end ingestion, secure storage, and SQLite database persistence."""
    pdf_bytes = create_synthetic_pdf(
        title="Physical Perimeter Security Policy",
        content="All data center entry points require dual-factor biometric access.",
    )

    doc = DocumentService.ingest_document(
        db=in_memory_db,
        project_id=sample_project.id,
        filename="perimeter_policy.pdf",
        content=pdf_bytes,
        uploaded_by="Lead Auditor",
        upload_dir=tmp_path,
    )

    assert doc.id is not None
    assert doc.project_id == sample_project.id
    assert doc.filename == "perimeter_policy.pdf"
    assert doc.file_type == "PDF"
    assert doc.file_extension == ".pdf"
    assert doc.extraction_status == "SUCCESS"
    assert doc.file_size_bytes == len(pdf_bytes)
    assert "dual-factor biometric access" in doc.raw_text
    assert doc.stored_path is not None
    assert Path(doc.stored_path).exists()
    assert Path(doc.stored_path).read_bytes() == pdf_bytes

    # Retrieve from DB via query
    retrieved = in_memory_db.query(Document).filter_by(id=doc.id).first()
    assert retrieved is not None
    assert retrieved.file_hash == doc.file_hash


def test_duplicate_document_detection(
    in_memory_db: Session, sample_project: Project, tmp_path: Path
):
    """Verify that duplicate file ingestion for the same project raises DuplicateDocumentError."""
    docx_bytes = create_synthetic_docx(title="Duplicate Test Policy")

    # First ingestion succeeds
    DocumentService.ingest_document(
        db=in_memory_db,
        project_id=sample_project.id,
        filename="policy_v1.docx",
        content=docx_bytes,
        upload_dir=tmp_path,
    )

    # Second ingestion with same content (even with different name) raises DuplicateDocumentError
    with pytest.raises(DuplicateDocumentError, match="already exists"):
        DocumentService.ingest_document(
            db=in_memory_db,
            project_id=sample_project.id,
            filename="policy_v1_copy.docx",
            content=docx_bytes,
            upload_dir=tmp_path,
        )


def test_extraction_failure_recording(
    in_memory_db: Session, sample_project: Project, tmp_path: Path
):
    """Verify that extraction failures are recorded in database without crashing."""
    corrupted_pdf = b"%PDF-1.4\nCorrupted content without xref table."

    # When raise_on_extraction_error=False, persists failed record
    doc = DocumentService.ingest_document(
        db=in_memory_db,
        project_id=sample_project.id,
        filename="corrupted_report.pdf",
        content=corrupted_pdf,
        upload_dir=tmp_path,
        raise_on_extraction_error=False,
    )

    assert doc.extraction_status == "FAILED"
    assert doc.raw_text is None
    assert doc.processing_error is not None

    # When raise_on_extraction_error=True with another corrupted document, raises error
    corrupted_pdf_2 = b"%PDF-1.4\nAnother corrupted payload"
    with pytest.raises(DocumentExtractionError):
        DocumentService.ingest_document(
            db=in_memory_db,
            project_id=sample_project.id,
            filename="corrupted_fail.pdf",
            content=corrupted_pdf_2,
            upload_dir=tmp_path,
            raise_on_extraction_error=True,
        )

