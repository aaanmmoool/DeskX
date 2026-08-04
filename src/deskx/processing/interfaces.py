"""Abstract interfaces for the processing layer.

These contracts define what each adapter or service must implement.
Concrete implementations live in the ``adapters`` or ``services`` packages.

Design notes
------------
* The ``FileAdapter`` ABC uses ``pandas.DataFrame`` as the data interchange
  type.  This keeps adapters thin and lets the processing engine work with
  a single, well-understood data structure.
* All methods that touch the filesystem accept ``Path`` objects — never raw
  strings — to prevent path-separator bugs on Windows.
* The ``preview`` method accepts a ``max_rows`` parameter so the GUI can
  request a lightweight sample without loading the full file.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import pandas as pd


class FileAdapter(ABC):
    """Read and write a single file format via Pandas.

    Subclass contract
    -----------------
    * ``extensions`` — the set of lowercase extensions this adapter handles
      (e.g. ``{".csv"}``).
    * ``read_preview`` — return at most *max_rows* rows for the preview table.
    * ``read_full`` — return the complete ``DataFrame``.
    * ``write`` — persist a ``DataFrame`` to *output_path* in the native format.
    * ``copy_file`` — byte-level copy from source to dest.
    """

    # ── Identity ────────────────────────────────────────────────────
    @property
    @abstractmethod
    def extensions(self) -> frozenset[str]:
        """Lowercase file extensions handled by this adapter."""

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable format name, e.g. ``'CSV'``."""

    # ── Reading ─────────────────────────────────────────────────────
    @abstractmethod
    def read_preview(
        self,
        path: Path,
        max_rows: int = 200,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """Return a preview DataFrame with at most *max_rows* rows.

        Supported kwargs (adapter-dependent):
        - ``header_row``: int or None — which row is the header
        - ``sheet_name``: str or int — worksheet name/index (XLSX)
        - ``delimiter``: str — column delimiter (TXT)
        """

    @abstractmethod
    def read_full(self, path: Path, **kwargs: Any) -> pd.DataFrame:
        """Return the complete DataFrame (may be large).

        Supports the same kwargs as ``read_preview``.
        """

    # ── Writing ─────────────────────────────────────────────────────
    @abstractmethod
    def write(
        self,
        df: pd.DataFrame,
        output_path: Path,
        **kwargs: Any,
    ) -> None:
        """Write *df* to *output_path* in the adapter's native format."""

    # ── Byte-level copy ─────────────────────────────────────────────
    @abstractmethod
    def copy_file(self, source: Path, destination: Path) -> None:
        """Byte-level copy from *source* to *destination*."""

    # ── Optional capabilities ───────────────────────────────────────

    def get_sheet_names(self, path: Path) -> list[str]:
        """Return worksheet names (XLSX only).  Default: empty list."""
        return []

    def detect_delimiter(self, path: Path) -> str | None:
        """Auto-detect the column delimiter (TXT only).  Default: None."""
        return None
