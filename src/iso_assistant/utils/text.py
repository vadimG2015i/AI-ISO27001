"""Text normalization and chunking utilities."""

import re


def clean_whitespace(text: str) -> str:
    """Normalizes excessive whitespace, carriage returns, and control characters."""
    if not text:
        return ""
    # Standardize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Replace multiple spaces/tabs with a single space
    text = re.sub(r"[ \t]+", " ", text)
    # Condense 3+ newlines to 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def chunk_text(text: str, chunk_size: int = 2000, overlap: int = 200) -> list[str]:
    """Splits long text into overlapping sliding-window chunks for LLM context injection."""
    cleaned = clean_whitespace(text)
    if not cleaned:
        return []

    if len(cleaned) <= chunk_size:
        return [cleaned]

    chunks: list[str] = []
    start = 0
    step = chunk_size - overlap

    while start < len(cleaned):
        end = min(start + chunk_size, len(cleaned))
        chunk = cleaned[start:end]
        chunks.append(chunk)
        if end == len(cleaned):
            break
        start += step

    return chunks

