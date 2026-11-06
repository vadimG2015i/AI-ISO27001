"""File validation and upload security module.

Enforces strict defense-in-depth security checks on all uploaded compliance artifacts:
1. Path traversal and filename sanitization.
2. File size enforcement.
3. Magic byte inspection (detecting MIME spoofing).
4. SHA-256 cryptographic hashing for integrity & deduplication.
5. Extensible anti-malware scanner hook.
"""

import hashlib
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar

from iso_assistant.config import settings


@dataclass(frozen=True)
class ValidationResult:
    """Immutable result of a file security validation check."""

    is_valid: bool
    sanitized_filename: str
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
        """Sanitizes user-provided filename to prevent path traversal and shell injection."""
        base_name = os.path.basename(filename)
        # Strip path navigation sequences
        base_name = base_name.replace("..", "").replace("/", "").replace("\\", "")
        # Remove null bytes and non-printable characters
        sanitized = re.sub(r"[^\w\s\.-]", "_", base_name).strip()
        if not sanitized or sanitized.startswith("."):
            sanitized = f"upload_{sanitized}"
        return sanitized

    @classmethod
    def compute_sha256(cls, content: bytes) -> str:
        """Computes the SHA-256 cryptographic digest of raw document bytes."""
        return hashlib.sha256(content).hexdigest()

    @classmethod
    def validate_file(cls, filename: str, content: bytes) -> ValidationResult:
        """Performs comprehensive security validation on an uploaded file buffer."""
        sanitized_name = cls.sanitize_filename(filename)
        file_size = len(content)
        file_hash = cls.compute_sha256(content)

        # 1. Size check
        if file_size == 0:
            return ValidationResult(
                is_valid=False,
                sanitized_filename=sanitized_name,
                file_size_bytes=0,
                sha256_hash=file_hash,
                detected_mime_type="application/octet-stream",
                error_message="Uploaded file is empty (0 bytes).",
            )

        if file_size > settings.max_file_size_bytes:
            max_mb = settings.max_file_size_bytes / (1024 * 1024)
            return ValidationResult(
                is_valid=False,
                sanitized_filename=sanitized_name,
                file_size_bytes=file_size,
                sha256_hash=file_hash,
                detected_mime_type="application/octet-stream",
                error_message=f"File exceeds maximum allowed upload size ({max_mb:.1f} MB).",
            )

        # 2. Extension check
        ext = Path(sanitized_name).suffix.lower()
        if ext not in settings.allowed_extensions:
            return ValidationResult(
                is_valid=False,
                sanitized_filename=sanitized_name,
                file_size_bytes=file_size,
                sha256_hash=file_hash,
                detected_mime_type="application/octet-stream",
                error_message=f"Disallowed file extension '{ext}'. Permitted: {settings.allowed_extensions}",
            )

        # 3. Magic byte verification (MIME spoofing prevention)
        expected_mime = cls.EXTENSION_MIME_MAP.get(ext, "application/octet-stream")
        valid_signatures = cls.MAGIC_SIGNATURES.get(expected_mime, [])
        header = content[:16]

        has_valid_signature = any(header.startswith(sig) for sig in valid_signatures)
        if not has_valid_signature:
            return ValidationResult(
                is_valid=False,
                sanitized_filename=sanitized_name,
                file_size_bytes=file_size,
                sha256_hash=file_hash,
                detected_mime_type="application/octet-stream",
                error_message=f"File header mismatch: content does not match expected format for '{ext}'.",
            )

        # 4. Optional Antivirus / Malware scanning hook
        if not cls._scan_for_malware(content):
            return ValidationResult(
                is_valid=False,
                sanitized_filename=sanitized_name,
                file_size_bytes=file_size,
                sha256_hash=file_hash,
                detected_mime_type=expected_mime,
                error_message="Security alert: file failed malware/heuristic inspection.",
            )

        return ValidationResult(
            is_valid=True,
            sanitized_filename=sanitized_name,
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
        # Baseline heuristic: check for embedded executable signatures or script macros
        # In production, this integrates with Windows Defender, ClamAV, or VirusTotal API
        forbidden_patterns = [
            b"MZ\x90\x00",  # Embedded PE Windows Executable
            b"#!/bin/sh",    # Embedded shell script
        ]
        return not any(pat in content for pat in forbidden_patterns)

