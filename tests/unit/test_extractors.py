"""Unit tests for extractor factory resolution."""

import pytest

from iso_assistant.extractors.docx_extractor import DocxExtractor
from iso_assistant.extractors.factory import ExtractorFactory
from iso_assistant.extractors.pdf_extractor import PdfExtractor
from iso_assistant.extractors.xlsx_extractor import XlsxExtractor


def test_extractor_factory_resolution():
    """Verify that file extensions resolve to appropriate extractor subclasses."""
    assert isinstance(ExtractorFactory.get_extractor("policy.pdf"), PdfExtractor)
    assert isinstance(ExtractorFactory.get_extractor("procedure.docx"), DocxExtractor)
    assert isinstance(ExtractorFactory.get_extractor("risk_register.xlsx"), XlsxExtractor)


def test_unsupported_file_extension_raises_error():
    """Verify that unsupported extensions raise a descriptive ValueError."""
    with pytest.raises(ValueError, match="Unsupported document format"):
        ExtractorFactory.get_extractor("script.sh")

