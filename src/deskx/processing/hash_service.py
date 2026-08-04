"""SHA-256 streaming hash service.

Computes file hashes using a configurable buffer size so that even
multi-gigabyte files can be hashed without excessive memory usage.

This module has **no PySide6 dependency**.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from deskx.core.config import HASH_ALGORITHM, HASH_BUFFER_SIZE


class HashService:
    """Compute and compare file hashes."""

    def __init__(
        self,
        algorithm: str = HASH_ALGORITHM,
        buffer_size: int = HASH_BUFFER_SIZE,
    ) -> None:
        self._algorithm = algorithm
        self._buffer_size = buffer_size

    # ── Public API ──────────────────────────────────────────────────

    def compute(self, path: Path) -> str:
        """Return the hex-digest of *path*.

        Raises
        ------
        FileNotFoundError
            If *path* does not exist.
        PermissionError
            If the file is not readable.
        """
        hasher = hashlib.new(self._algorithm)
        with open(path, "rb") as fh:
            while True:
                chunk = fh.read(self._buffer_size)
                if not chunk:
                    break
                hasher.update(chunk)
        return hasher.hexdigest()

    def verify(self, path: Path, expected_hash: str) -> bool:
        """Return ``True`` if *path* hashes to *expected_hash*."""
        return self.compute(path) == expected_hash
