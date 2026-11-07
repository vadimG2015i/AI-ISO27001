"""PDF document extraction implementation using pdfplumber and pypdf."""

import io
from typing import Any

import pdfplumber
from pdfplumber.utils.exceptions import PdfminerException
from pypdf import PdfReader
from pypdf.errors import PdfReadError

from iso_assistant.extractors.base import (
    AbstractBaseExtractor,
    DocumentExtractionError,
    ExtractedDocument,
)
from iso_assistant.utils.logger import get_logger

logger = get_logger(__name__)


class PdfExtractor(AbstractBaseExtractor):
    """Extractor for Adobe Portable Document Format (.pdf) files."""

    def extract(self, content: bytes, filename: str) -> ExtractedDocument:
        """Extracts text, structural tables, and metadata from PDF binary content.

        Attempts high-fidelity extraction via pdfplumber, falling back to pypdf if needed.
        Handles empty or encrypted PDFs gracefully. OCR is intentionally not implemented.
        """
        if not content:
            raise DocumentExtractionError("PDF content is empty (0 bytes).")

        extracted_pages_text: list[str] = []
        extracted_tables: list[list[list[str]]] = []
        metadata: dict[str, Any] = {}
        warnings: list[str] = []
        page_count = 0

        # Primary extraction using pdfplumber
        try:
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                page_count = len(pdf.pages)
                if pdf.metadata:
                    metadata = {
                        k: str(v)
                        for k, v in pdf.metadata.items()
                        if v is not None
                    }

                for page_idx, page in enumerate(pdf.pages, start=1):
                    page_text = page.extract_text() or ""
                    if page_text.strip():
                        extracted_pages_text.append(f"--- Page {page_idx} ---\n{page_text.strip()}")

                    # Extract tabular structures if present
                    try:
                        tables = page.extract_tables()
                        for table in tables:
                            if table:
                                # Clean cells
                                cleaned_table = [
                                    [str(cell).strip() if cell is not None else "" for cell in row]
                                    for row in table
                                ]
                                extracted_tables.append(cleaned_table)
                    except (ValueError, AttributeError) as tbl_err:
                        logger.warning("Table extraction warning on page %d: %s", page_idx, tbl_err)
                        warnings.append(f"Table extraction skipped on page {page_idx}: {tbl_err}")

        except (OSError, ValueError, PdfminerException) as plumber_err:
            logger.warning("pdfplumber encountered error on %s: %s. Attempting pypdf fallback.", filename, plumber_err)
            # Fallback extraction using pypdf
            try:
                reader = PdfReader(io.BytesIO(content))
                page_count = len(reader.pages)
                if reader.metadata:
                    metadata = {k: str(v) for k, v in reader.metadata.items() if v is not None}

                for page_idx, page in enumerate(reader.pages, start=1):
                    page_text = page.extract_text() or ""
                    if page_text.strip():
                        extracted_pages_text.append(f"--- Page {page_idx} ---\n{page_text.strip()}")
            except (PdfReadError, ValueError, OSError) as pypdf_err:
                raise DocumentExtractionError(
                    f"Failed to parse PDF document '{filename}': {pypdf_err}"
                ) from pypdf_err

        full_text = "\n\n".join(extracted_pages_text).strip()
        status = "SUCCESS" if full_text else "EMPTY"
        if status == "EMPTY":
            warnings.append("Document processed successfully but contains no extractable text (scanned image or empty pages).")

        return ExtractedDocument(
            filename=filename,
            raw_text=full_text,
            file_type="PDF",
            page_count=page_count,
            tables=extracted_tables,
            metadata=metadata,
            warnings=warnings,
            extraction_status=status,
        )
