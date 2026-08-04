"""Plain-text / delimited file adapter.

Reads tab-separated or custom-delimited text files through Pandas.
Supports runtime delimiter configuration and auto-detection.
"""

from __future__ import annotations

import csv
import shutil
from pathlib import Path
from typing import Any

import pandas as pd

from deskx.processing.interfaces import FileAdapter


class TxtAdapter(FileAdapter):
    """Read and write delimited text files."""

    def __init__(self, default_delimiter: str = "\t") -> None:
        self._default_delimiter = default_delimiter

    @property
    def extensions(self) -> frozenset[str]:
        return frozenset({".txt"})

    @property
    def display_name(self) -> str:
        return "Text (TXT)"

    # ── Reading ─────────────────────────────────────────────────────

    def read_preview(
        self,
        path: Path,
        max_rows: int = 200,
        **kwargs: Any,
    ) -> pd.DataFrame:
        delimiter = kwargs.get("delimiter", self._default_delimiter)
        header_row = kwargs.get("header_row", 0)
        return pd.read_csv(
            path,
            sep=delimiter,
            nrows=max_rows,
            header=header_row,
            engine="python",
        )

    def read_full(self, path: Path, **kwargs: Any) -> pd.DataFrame:
        delimiter = kwargs.get("delimiter", self._default_delimiter)
        header_row = kwargs.get("header_row", 0)
        return pd.read_csv(
            path,
            sep=delimiter,
            header=header_row,
            engine="python",
        )

    # ── Writing ─────────────────────────────────────────────────────

    def write(
        self,
        df: pd.DataFrame,
        output_path: Path,
        **kwargs: Any,
    ) -> None:
        delimiter = kwargs.pop("delimiter", self._default_delimiter)
        df.to_csv(
            output_path,
            sep=delimiter,
            index=False,
            **kwargs,
        )

    # ── Copy ────────────────────────────────────────────────────────

    def copy_file(self, source: Path, destination: Path) -> None:
        shutil.copy2(source, destination)

    # ── Auto-detection ──────────────────────────────────────────────

    def detect_delimiter(self, path: Path) -> str | None:
        """Sniff the delimiter from the first few lines of the file.

        Returns the detected delimiter or ``None`` if detection fails.
        """
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                sample = fh.read(8192)
            dialect = csv.Sniffer().sniff(sample, delimiters="\t,;|")
            return dialect.delimiter
        except (csv.Error, Exception):
            return None
