"""Extractor factory for dynamic parser resolution based on file extension."""

from pathlib import Path
from typing import ClassVar

from iso_assistant.extractors.base import AbstractBaseExtractor
from iso_assistant.extractors.docx_extractor import DocxExtractor
from iso_assistant.extractors.pdf_extractor import PdfExtractor
from iso_assistant.extractors.xlsx_extractor import XlsxExtractor


class ExtractorFactory:
    """Factory to dispatch appropriate document extractor based on filename extension."""

    _REGISTRY: ClassVar[dict[str, type[AbstractBaseExtractor]]] = {
        ".pdf": PdfExtractor,
        ".docx": DocxExtractor,
        ".xlsx": XlsxExtractor,
    }

    @classmethod
    def get_extractor(cls, filename: str) -> AbstractBaseExtractor:
        """Instantiates and returns the extractor suitable for the given filename.

        Args:
            filename: Name of the file with extension.

        Returns:
            Instance of AbstractBaseExtractor subclass.

        Raises:
            ValueError: If file extension is unsupported.
        """
        ext = Path(filename).suffix.lower()
        extractor_class = cls._REGISTRY.get(ext)
        if not extractor_class:
            raise ValueError(
                f"Unsupported document format '{ext}'. Supported formats: {list(cls._REGISTRY.keys())}"
            )
        return extractor_class()

