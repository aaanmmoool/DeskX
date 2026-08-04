"""Tests for adapters.xlsx_adapter module."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from deskx.adapters.xlsx_adapter import XlsxAdapter


@pytest.fixture
def _ensure_xlsx(sample_xlsx: Path, sample_df: pd.DataFrame):
    """Create the XLSX fixture if it doesn't exist yet."""
    if not sample_xlsx.exists():
        sample_df.to_excel(
            sample_xlsx, index=False, engine="openpyxl"
        )


@pytest.mark.usefixtures("_ensure_xlsx")
class TestXlsxAdapter:
    def setup_method(self):
        self.adapter = XlsxAdapter()

    def test_extensions(self):
        assert ".xlsx" in self.adapter.extensions

    def test_display_name(self):
        assert "XLSX" in self.adapter.display_name

    def test_read_preview(self, sample_xlsx: Path):
        df = self.adapter.read_preview(sample_xlsx, max_rows=3)
        assert isinstance(df, pd.DataFrame)
        assert len(df) <= 3

    def test_read_full(self, sample_xlsx: Path):
        df = self.adapter.read_full(sample_xlsx)
        assert len(df) == 5
        assert "name" in df.columns

    def test_write(self, sample_df: pd.DataFrame, tmp_path: Path):
        out = tmp_path / "written.xlsx"
        self.adapter.write(sample_df, out)
        assert out.exists()
        reloaded = pd.read_excel(out, engine="openpyxl")
        pd.testing.assert_frame_equal(reloaded, sample_df, check_dtype=False)

    def test_copy_file(self, sample_xlsx: Path, tmp_path: Path):
        dest = tmp_path / "copy.xlsx"
        self.adapter.copy_file(sample_xlsx, dest)
        assert dest.exists()
        assert dest.read_bytes() == sample_xlsx.read_bytes()
