"""Temporary-file lifecycle manager.

Ensures that output files are always written through a temporary file
in the **same directory** as the final output.  This prevents partial
writes from leaving behind corrupt files.

Usage::

    with TempFileManager(final_path) as tmp:
        # Write data to tmp.temp_path
        adapter.copy_file(source, tmp.temp_path)
        # On __exit__, the temp file is promoted to final_path
    # If an exception occurs, the temp file is deleted automatically.

This module has **no PySide6 dependency**.
"""

from __future__ import annotations

import logging
from pathlib import Path
from types import TracebackType
from typing import Self

from deskx.core.config import TEMP_FILE_PREFIX

logger = logging.getLogger(__name__)


class TempFileManager:
    """Context manager that writes through a temp file then renames.

    Parameters
    ----------
    final_path
        The desired output path.  The temp file is created in the same
        directory with a dotfile prefix so it is hidden on Unix and
        unlikely to collide on Windows.
    """

    def __init__(self, final_path: Path) -> None:
        self._final_path = final_path
        self._temp_path = final_path.parent / (
            TEMP_FILE_PREFIX + final_path.name
        )
        self._committed = False

    # ── Properties ──────────────────────────────────────────────────

    @property
    def temp_path(self) -> Path:
        """The temporary file path that callers should write to."""
        return self._temp_path

    @property
    def final_path(self) -> Path:
        """The intended final output path."""
        return self._final_path

    # ── Context manager ─────────────────────────────────────────────

    def __enter__(self) -> Self:
        # If a stale temp file exists from a crashed run, remove it.
        if self._temp_path.exists():
            logger.warning(
                "Removing stale temp file: %s", self._temp_path
            )
            self._temp_path.unlink()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if exc_type is None and self._temp_path.exists():
            # Success — promote temp → final.
            self._promote()
        else:
            # Failure — clean up the temp file.
            self._cleanup()

    # ── Internal ────────────────────────────────────────────────────

    def _promote(self) -> None:
        """Rename the temp file to the final path."""
        # If final already exists (shouldn't in normal flow), remove it.
        if self._final_path.exists():
            self._final_path.unlink()
        self._temp_path.rename(self._final_path)
        self._committed = True
        logger.info("Promoted temp file → %s", self._final_path)

    def _cleanup(self) -> None:
        """Delete the temp file if it exists."""
        if self._temp_path.exists():
            try:
                self._temp_path.unlink()
                logger.info("Cleaned up temp file: %s", self._temp_path)
            except OSError:
                logger.exception(
                    "Failed to clean up temp file: %s", self._temp_path
                )
