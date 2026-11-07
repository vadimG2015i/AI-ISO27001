"""Microsoft Excel (.xlsx) workbook extraction implementation using openpyxl."""

import io
from typing import Any

import openpyxl

from iso_assistant.extractors.base import (
    AbstractBaseExtractor,
    DocumentExtractionError,
    ExtractedDocument,
)
from iso_assistant.utils.logger import get_logger

logger = get_logger(__name__)


class XlsxExtractor(AbstractBaseExtractor):
    """Extractor for Microsoft Excel (.xlsx) OpenXML spreadsheet workbooks."""

    def extract(self, content: bytes, filename: str) -> ExtractedDocument:
        """Extracts tabular worksheets, cell values, and sheet names from Excel OpenXML binary content.

        Preserves worksheet boundaries and tabular relationships for compliance policy and asset analysis.
        """
        if not content:
            raise DocumentExtractionError("XLSX content is empty (0 bytes).")

        try:
            # data_only=True extracts computed formula values rather than raw formula strings
            wb = openpyxl.load_workbook(io.BytesIO(content), data_only=True, read_only=True)
        except Exception as xlsx_err:
            raise DocumentExtractionError(
                f"Failed to open Excel workbook '{filename}': {xlsx_err}"
            ) from xlsx_err

        sheet_text_blocks: list[str] = []
        extracted_tables: list[list[list[str]]] = []
        warnings: list[str] = []
        sheet_count = len(wb.sheetnames)

        metadata: dict[str, Any] = {
            "sheet_names": wb.sheetnames,
            "total_sheets": sheet_count,
        }

        try:
            if wb.properties:
                for prop in ("creator", "title", "subject", "created", "modified"):
                    val = getattr(wb.properties, prop, None)
                    if val is not None:
                        metadata[prop] = str(val)
        except (AttributeError, ValueError):
            logger.debug("Could not read workbook properties metadata.")

        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            sheet_rows: list[list[str]] = []
            formatted_lines: list[str] = [f"--- Worksheet: {sheet_name} ---"]

            for row in ws.iter_rows(values_only=True):
                # Filter out completely empty rows
                if not any(cell is not None and str(cell).strip() != "" for cell in row):
                    continue

                cleaned_row = [str(cell).strip() if cell is not None else "" for cell in row]
                sheet_rows.append(cleaned_row)
                formatted_lines.append(" | ".join(cleaned_row))

            if sheet_rows:
                extracted_tables.append(sheet_rows)
                sheet_text_blocks.append("\n".join(formatted_lines))

        wb.close()

        full_text = "\n\n".join(sheet_text_blocks).strip()
        status = "SUCCESS" if full_text else "EMPTY"
        if status == "EMPTY":
            warnings.append("Workbook contains no readable tabular data or all sheets are blank.")

        return ExtractedDocument(
            filename=filename,
            raw_text=full_text,
            file_type="XLSX",
            page_count=max(1, sheet_count),
            sheet_count=sheet_count,
            tables=extracted_tables,
            metadata=metadata,
            warnings=warnings,
            extraction_status=status,
        )
