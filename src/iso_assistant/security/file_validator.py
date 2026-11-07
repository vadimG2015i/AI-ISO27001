"""File validation and upload security module.

Enforces strict defense-in-depth security checks on all uploaded compliance artifacts:
1. Path traversal and filename sanitization.
2. File size enforcement.
3. Magic byte inspection (detecting MIME spoofing).
4. ZIP structure integrity verification for OpenXML (.docx, .xlsx).
5. SHA-256 cryptographic hashing for integrity & deduplication.
6. Extensible anti-malware and heuristic inspection hook.
"""

import hashlib
import io
import os
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar

from iso_assistant.config import settings


class DocumentValidationError(ValueError):
    """Raised when an uploaded document fails security or format validation."""


class DuplicateDocumentError(ValueError):
    """Raised when an identical document has already been ingested in the project."""


@dataclass(frozen=True)
class ValidationResult:
    """Immutable result of a file security validation check."""

    is_valid: bool
    sanitized_filename: str
    file_extension: str
    file_size_bytes: int
    sha256_hash: str
    detected_mime_type: str
    error_message: str | None = None


class FileValidator:
    """Security validator for ingested compliance documents."""

    # Magic byte signatures
    MAGIC_SIGNATURES: ClassVar[dict[str, list[bytes]]] = {
        "application/pdf": [b"%PDF-"],
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [b"PK\x03\x04"],
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [b"PK\x03\x04"],
    }

    # Extension to expected MIME mapping
    EXTENSION_MIME_MAP: ClassVar[dict[str, str]] = {
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }

    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        r"""Sanitizes user-provided filename to prevent path traversal and shell injection.

        - Strips directory path components (both UNIX / and Windows \).
        - Removes path traversal sequences ('..').
        - Removes null bytes and non-printable control characters.
        - Replaces special characters with underscores while preserving dots and dashes.
        - Ensures safe fallback if filename becomes empty or starts with a dot.
        """
        # Remove null bytes immediately
        filename = filename.replace("\x00", "")
        # Get base name and strip slashes
        base_name = os.path.basename(filename)
        base_name = base_name.replace("..", "").replace("/", "").replace("\\", "")
        # Remove control characters and non-whitelisted characters
        sanitized = re.sub(r"[^\w\s\.-]", "_", base_name).strip()
        # Collapse multiple spaces or underscores
        sanitized = re.sub(r"[_\s]+", "_", sanitized)
        # Prevent hidden files (leading dot) or empty filenames
        if not sanitized or sanitized.startswith("."):
            sanitized = f"upload_{sanitized.lstrip('.')}"
        return sanitized

    @classmethod
    def compute_sha256(cls, content: bytes) -> str:
        """Computes the SHA-256 cryptographic digest of raw document bytes."""
        return hashlib.sha256(content).hexdigest()

    @classmethod
    def generate_safe_storage_name(cls, sanitized_filename: str, sha256_hash: str) -> str:
        """Generates collision-free, secure storage filename prefixed with a hash digest."""
        ext = Path(sanitized_filename).suffix.lower()
        stem = Path(sanitized_filename).stem[:40]
        return f"{sha256_hash[:16]}_{stem}{ext}"

    @classmethod
    def validate_file(cls, filename: str, content: bytes) -> ValidationResult:
        """Performs comprehensive security validation on an uploaded file buffer.

        Never trusts user-provided filename or MIME header.
        """
        sanitized_name = cls.sanitize_filename(filename)
        file_size = len(content)
        file_hash = cls.compute_sha256(content)
        ext = Path(sanitized_name).suffix.lower()

        # 1. Size check: Empty file
        if file_size == 0:
            return ValidationResult(
                is_valid=False,
                sanitized_filename=sanitized_name,
                file_extension=ext,
                file_size_bytes=0,
                sha256_hash=file_hash,
                detected_mime_type="application/octet-stream",
                error_message="Uploaded file is empty (0 bytes).",
            )

        # 2. Size check: Exceeds threshold
        if file_size > settings.max_file_size_bytes:
            max_mb = settings.max_file_size_bytes / (1024 * 1024)
            return ValidationResult(
                is_valid=False,
                sanitized_filename=sanitized_name,
                file_extension=ext,
                file_size_bytes=file_size,
                sha256_hash=file_hash,
                detected_mime_type="application/octet-stream",
                error_message=f"File exceeds maximum allowed upload size ({max_mb:.1f} MB).",
            )

        # 3. Extension check
        if ext not in settings.allowed_extensions:
            return ValidationResult(
                is_valid=False,
                sanitized_filename=sanitized_name,
                file_extension=ext,
                file_size_bytes=file_size,
                sha256_hash=file_hash,
                detected_mime_type="application/octet-stream",
                error_message=f"Disallowed file extension '{ext}'. Permitted: {settings.allowed_extensions}",
            )

        # 4. Magic byte verification (MIME spoofing prevention)
        expected_mime = cls.EXTENSION_MIME_MAP.get(ext, "application/octet-stream")
        valid_signatures = cls.MAGIC_SIGNATURES.get(expected_mime, [])
        header = content[:16]

        has_valid_signature = any(header.startswith(sig) for sig in valid_signatures)
        if not has_valid_signature:
            return ValidationResult(
                is_valid=False,
                sanitized_filename=sanitized_name,
                file_extension=ext,
                file_size_bytes=file_size,
                sha256_hash=file_hash,
                detected_mime_type="application/octet-stream",
                error_message=f"File header mismatch: content does not match expected format for '{ext}'.",
            )

        # 5. OpenXML ZIP container integrity verification
        if ext in (".docx", ".xlsx"):
            try:
                with zipfile.ZipFile(io.BytesIO(content)) as zf:
                    # Test zip archive integrity
                    bad_file = zf.testzip()
                    if bad_file:
                        return ValidationResult(
                            is_valid=False,
                            sanitized_filename=sanitized_name,
                            file_extension=ext,
                            file_size_bytes=file_size,
                            sha256_hash=file_hash,
                            detected_mime_type=expected_mime,
                            error_message=f"Malformed OpenXML document: corrupted archive member '{bad_file}'.",
                        )
            except zipfile.BadZipFile:
                return ValidationResult(
                    is_valid=False,
                    sanitized_filename=sanitized_name,
                    file_extension=ext,
                    file_size_bytes=file_size,
                    sha256_hash=file_hash,
                    detected_mime_type=expected_mime,
                    error_message=f"Malformed OpenXML document: invalid ZIP structure for '{ext}'.",
                )

        # 6. Antivirus / Malware heuristic scanning hook
        if not cls._scan_for_malware(content):
            return ValidationResult(
                is_valid=False,
                sanitized_filename=sanitized_name,
                file_extension=ext,
                file_size_bytes=file_size,
                sha256_hash=file_hash,
                detected_mime_type=expected_mime,
                error_message="Security alert: file failed malware/heuristic inspection.",
            )

        return ValidationResult(
            is_valid=True,
            sanitized_filename=sanitized_name,
            file_extension=ext,
            file_size_bytes=file_size,
            sha256_hash=file_hash,
            detected_mime_type=expected_mime,
            error_message=None,
        )

    @classmethod
    def _scan_for_malware(cls, content: bytes) -> bool:
        """Pluggable hook for local antivirus or heuristic threat scanner.

        Returns True if safe, False if malicious pattern detected.
        """
        forbidden_patterns = [
            b"MZ\x90\x00",  # Embedded PE Windows Executable
            b"#!/bin/sh",    # Embedded shell script
            b"powershell.exe -enc",
        ]
        return not any(pat in content for pat in forbidden_patterns)
