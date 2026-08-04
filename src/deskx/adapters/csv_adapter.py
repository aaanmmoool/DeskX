"""CSV file adapter.

Uses Pandas ``read_csv`` / ``to_csv``.  Supports header row selection
and encoding detection.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

import pandas as pd

from deskx.processing.interfaces import FileAdapter


class CsvAdapter(FileAdapter):
    """Read and write CSV files."""

    @property
    def extensions(self) -> frozenset[str]:
        return frozenset({".csv"})

    @property
    def display_name(self) -> str:
        return "CSV"

    # ── Reading ─────────────────────────────────────────────────────

    def read_preview(
        self,
        path: Path,
        max_rows: int = 200,
        **kwargs: Any,
    ) -> pd.DataFrame:
        header_row = kwargs.get("header_row", 0)
        encoding = kwargs.get("encoding", "utf-8")
        try:
            return pd.read_csv(
                path,
                nrows=max_rows,
                header=header_row,
                encoding=encoding,
            )
        except UnicodeDecodeError:
            return pd.read_csv(
                path,
                nrows=max_rows,
                header=header_row,
                encoding="latin-1",
            )

    def read_full(self, path: Path, **kwargs: Any) -> pd.DataFrame:
        header_row = kwargs.get("header_row", 0)
        encoding = kwargs.get("encoding", "utf-8")
        try:
            return pd.read_csv(
                path,
                header=header_row,
                encoding=encoding,
            )
        except UnicodeDecodeError:
            return pd.read_csv(
                path,
                header=header_row,
                encoding="latin-1",
            )

    # ── Writing ─────────────────────────────────────────────────────

    def write(
        self,
        df: pd.DataFrame,
        output_path: Path,
        **kwargs: Any,
    ) -> None:
        df.to_csv(output_path, index=False, **kwargs)

    # ── Copy ────────────────────────────────────────────────────────

    def copy_file(self, source: Path, destination: Path) -> None:
        shutil.copy2(source, destination)
