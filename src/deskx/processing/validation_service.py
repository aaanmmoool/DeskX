"""Pre- and post-processing validation service.

Guards against common safety violations:

* Source and output paths resolving to the same file.
* Output directory being missing or not writable.
* Output file not existing after processing.

This module has **no PySide6 dependency**.
"""

from __future__ import annotations

import os
from pathlib import Path

from deskx.core.exceptions import (
    OutputDirectoryError,
    SamePathError,
    ValidationError,
)


class ValidationService:
    """Validates filesystem preconditions and postconditions."""

    # ── Pre-processing checks ───────────────────────────────────────

    @staticmethod
    def validate_paths(source: Path, output: Path) -> None:
        """Raise if *source* and *output* resolve to the same file.

        Also verifies that the output's parent directory exists and is
        writable.
        """
        if source.resolve() == output.resolve():
            raise SamePathError(str(source))

        output_dir = output.parent
        if not output_dir.exists():
            raise OutputDirectoryError(
                f"Output directory does not exist: '{output_dir}'"
            )
        if not os.access(output_dir, os.W_OK):
            raise OutputDirectoryError(
                f"Output directory is not writable: '{output_dir}'"
            )

    @staticmethod
    def validate_source_exists(source: Path) -> None:
        """Raise if the source file does not exist."""
        if not source.is_file():
            raise ValidationError(
                f"Source file does not exist: '{source}'"
            )

    # ── Post-processing checks ──────────────────────────────────────

    @staticmethod
    def validate_output_exists(output: Path) -> None:
        """Raise if the output file was not created."""
        if not output.is_file():
            raise ValidationError(
                f"Output file was not created: '{output}'"
            )

    @staticmethod
    def validate_output_non_empty(output: Path) -> None:
        """Raise if the output file is empty."""
        if output.stat().st_size == 0:
            raise ValidationError(
                f"Output file is empty: '{output}'"
            )
