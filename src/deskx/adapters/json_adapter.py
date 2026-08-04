"""JSON file adapter.

Handles both standard JSON (records-oriented array) and line-delimited
JSON.  Detects the format automatically by peeking at the first
non-whitespace character.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

import pandas as pd

from deskx.processing.interfaces import FileAdapter


class JsonAdapter(FileAdapter):
    """Read and write JSON files."""

    @property
    def extensions(self) -> frozenset[str]:
        return frozenset({".json"})

    @property
    def display_name(self) -> str:
        return "JSON"

    # ── Reading ─────────────────────────────────────────────────────

    def read_preview(
        self,
        path: Path,
        max_rows: int = 200,
        **kwargs: Any,
    ) -> pd.DataFrame:
        df = self._read(path)
        return df.head(max_rows)

    def read_full(self, path: Path, **kwargs: Any) -> pd.DataFrame:
        return self._read(path)

    # ── Writing ─────────────────────────────────────────────────────

    def write(
        self,
        df: pd.DataFrame,
        output_path: Path,
        **kwargs: Any,
    ) -> None:
        df.to_json(
            output_path,
            orient="records",
            indent=2,
            force_ascii=False,
            **kwargs,
        )

    # ── Copy ────────────────────────────────────────────────────────

    def copy_file(self, source: Path, destination: Path) -> None:
        shutil.copy2(source, destination)

    # ── Internal ────────────────────────────────────────────────────

    @staticmethod
    def _is_line_delimited(path: Path) -> bool:
        """Return ``True`` if the file looks like newline-delimited JSON."""
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                stripped = line.strip()
                if stripped:
                    # Standard JSON arrays/objects start with [ or {
                    # Line-delimited JSON has one object per line
                    return not stripped.startswith("[")
        return False

    @staticmethod
    def _read(path: Path) -> pd.DataFrame:
        """Read a JSON file, auto-detecting orientation."""
        if JsonAdapter._is_line_delimited(path):
            return pd.read_json(path, lines=True, encoding="utf-8")
        try:
            return pd.read_json(path, orient="records", encoding="utf-8")
        except ValueError:
            return pd.read_json(path, lines=True, encoding="utf-8")
