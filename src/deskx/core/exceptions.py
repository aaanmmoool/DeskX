"""Typed exception hierarchy for DeskX.

Every custom exception inherits from :class:`DeskXError` so callers can
catch at any level of specificity.
"""

from __future__ import annotations


class DeskXError(Exception):
    """Base exception for all DeskX errors."""


# ── File adapter errors ─────────────────────────────────────────────

class FileAdapterError(DeskXError):
    """Raised when a file adapter cannot read or write a file."""


class UnsupportedFormatError(FileAdapterError):
    """Raised when the file extension has no registered adapter."""

    def __init__(self, extension: str) -> None:
        self.extension = extension
        super().__init__(f"Unsupported file format: '{extension}'")


# ── Validation errors ───────────────────────────────────────────────

class ValidationError(DeskXError):
    """Raised when a pre- or post-processing validation fails."""


class SamePathError(ValidationError):
    """Raised when source and output paths resolve to the same file."""

    def __init__(self, path: str) -> None:
        self.path = path
        super().__init__(
            f"Source and output paths must differ: '{path}'"
        )


class OutputDirectoryError(ValidationError):
    """Raised when the output directory is missing or not writable."""


# ── Hash errors ──────────────────────────────────────────────────────

class HashMismatchError(DeskXError):
    """Raised when the source file hash changes during processing."""

    def __init__(
        self,
        expected: str,
        actual: str,
        path: str,
    ) -> None:
        self.expected = expected
        self.actual = actual
        self.path = path
        super().__init__(
            f"Hash mismatch for '{path}': "
            f"expected {expected}, got {actual}"
        )


# ── Processing errors ───────────────────────────────────────────────

class ProcessingError(DeskXError):
    """Raised when the processing pipeline encounters an error."""


class CancellationError(DeskXError):
    """Raised when the user cancels a running job."""
