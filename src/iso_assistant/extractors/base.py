"""Abstract base extractor and data structures for parsed compliance documents."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


class DocumentExtractionError(ValueError):
    """Raised when document content parsing fails due to corruption or malformed syntax."""


@dataclass
class ExtractedDocument:
    """Standardized representation of parsed compliance documents across all file types."""

    filename: str
    raw_text: str
    file_type: str = ""
    page_count: int = 1
    sheet_count: int = 0
    tables: list[list[list[str]]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    extraction_status: str = "SUCCESS"  # "SUCCESS", "EMPTY", "PARTIAL", "FAILED"
    error_message: str | None = None

    @property
    def extracted_text(self) -> str:
        """Alias for raw_text to provide consistent interface."""
        return self.raw_text

    @property
    def original_filename(self) -> str:
        """Alias for filename."""
        return self.filename

    @property
    def character_count(self) -> int:
        """Returns total character count of extracted text."""
        return len(self.raw_text)

    @property
    def estimated_word_count(self) -> int:
        """Rough estimation of word count."""
        return len(self.raw_text.split())

    @property
    def table_count(self) -> int:
        """Returns total count of structural tables discovered."""
        return len(self.tables)


class AbstractBaseExtractor(ABC):
    """Contract that all document format extractors must implement."""

    @abstractmethod
    def extract(self, content: bytes, filename: str) -> ExtractedDocument:
        """Extracts text, structural tables, and metadata from document raw bytes.

        Args:
            content: Raw binary content of the file.
            filename: Original sanitized filename.

        Returns:
            ExtractedDocument instance containing standardized extracted content.

        Raises:
            DocumentExtractionError: If file content is corrupted or unreadable.
        """
