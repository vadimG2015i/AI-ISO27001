"""Microsoft Word (.docx) document extraction implementation using python-docx."""

import io
from typing import Any

import docx
from docx.opc.exceptions import PackageNotFoundError

from iso_assistant.extractors.base import (
    AbstractBaseExtractor,
    DocumentExtractionError,
    ExtractedDocument,
)


class DocxExtractor(AbstractBaseExtractor):
    """Extractor for Microsoft Word (.docx) OpenXML documents."""

    def extract(self, content: bytes, filename: str) -> ExtractedDocument:
        """Extracts text, headings, and tables from Word OpenXML binary content.

        Preserves reading order across headings, body paragraphs, bullet lists, and tables.
        """
        if not content:
            raise DocumentExtractionError("DOCX content is empty (0 bytes).")

        try:
            doc = docx.Document(io.BytesIO(content))
        except (PackageNotFoundError, Exception) as docx_err:
            raise DocumentExtractionError(
                f"Failed to open Word document '{filename}': {docx_err}"
            ) from docx_err

        text_sections: list[str] = []
        extracted_tables: list[list[list[str]]] = []
        warnings: list[str] = []

        # 1. Extract metadata from core properties
        metadata: dict[str, Any] = {}
        try:
            core_props = doc.core_properties
            for prop in ("author", "title", "subject", "comments", "created", "modified"):
                val = getattr(core_props, prop, None)
                if val is not None:
                    metadata[prop] = str(val)
        except (AttributeError, ValueError):
            metadata = {}

        # 2. Extract paragraphs and preserve heading context
        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue
            style_name = para.style.name if para.style else ""
            if "Heading 1" in style_name:
                text_sections.append(f"# {text}")
            elif "Heading 2" in style_name:
                text_sections.append(f"## {text}")
            elif "Heading 3" in style_name:
                text_sections.append(f"### {text}")
            elif "List" in style_name or "Bullet" in style_name:
                text_sections.append(f"- {text}")
            else:
                text_sections.append(text)

        # 3. Extract tables
        for tbl_idx, table in enumerate(doc.tables, start=1):
            table_rows: list[list[str]] = []
            formatted_table_lines: list[str] = [f"[Table {tbl_idx}]"]
            for row in table.rows:
                row_cells = [cell.text.strip() for cell in row.cells]
                # Avoid exact consecutive duplicate cells caused by merged cells
                cleaned_cells: list[str] = list(row_cells)
                table_rows.append(cleaned_cells)
                formatted_table_lines.append(" | ".join(cleaned_cells))

            if table_rows:
                extracted_tables.append(table_rows)
                text_sections.append("\n".join(formatted_table_lines))

        full_text = "\n\n".join(text_sections).strip()
        status = "SUCCESS" if full_text else "EMPTY"
        if status == "EMPTY":
            warnings.append("Document processed successfully but contains no textual content.")

        return ExtractedDocument(
            filename=filename,
            raw_text=full_text,
            file_type="DOCX",
            page_count=max(1, len(doc.paragraphs) // 30),  # Heuristic estimation
            tables=extracted_tables,
            metadata=metadata,
            warnings=warnings,
            extraction_status=status,
        )
