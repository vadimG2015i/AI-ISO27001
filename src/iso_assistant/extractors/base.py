"""Abstract base extractor and data structures for parsed compliance documents."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ExtractedDocument:
    """Standardized representation of parsed compliance documents across all file types."""

    filename: str
    raw_text: str
    page_count: int = 1
    tables: list[list[list[str]]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    @property
    def character_count(self) -> int:
        """Returns total character count of extracted raw text."""
        return len(self.raw_text)

    @property
    def estimated_word_count(self) -> int:
        """Rough estimation of word count."""
        return len(self.raw_text.split())


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
            ValueError: If file content is corrupted or unreadable.
        """

