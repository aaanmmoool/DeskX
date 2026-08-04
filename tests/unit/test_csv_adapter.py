"""Tests for adapters.csv_adapter module."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from deskx.adapters.csv_adapter import CsvAdapter


class TestCsvAdapter:
    def setup_method(self):
        self.adapter = CsvAdapter()

    def test_extensions(self):
        assert ".csv" in self.adapter.extensions

    def test_display_name(self):
        assert self.adapter.display_name == "CSV"

    def test_read_preview(self, sample_csv: Path):
        df = self.adapter.read_preview(sample_csv, max_rows=3)
        assert isinstance(df, pd.DataFrame)
        assert len(df) <= 3
        assert "name" in df.columns

    def test_read_full(self, sample_csv: Path):
        df = self.adapter.read_full(sample_csv)
        assert len(df) == 5
        assert list(df.columns) == [
            "id", "name", "email", "age", "salary"
        ]

    def test_write(self, sample_df: pd.DataFrame, tmp_path: Path):
        out = tmp_path / "written.csv"
        self.adapter.write(sample_df, out)
        assert out.exists()
        reloaded = pd.read_csv(out)
        pd.testing.assert_frame_equal(reloaded, sample_df)

    def test_copy_file(self, sample_csv: Path, tmp_path: Path):
        dest = tmp_path / "copy.csv"
        self.adapter.copy_file(sample_csv, dest)
        assert dest.exists()
        assert dest.read_bytes() == sample_csv.read_bytes()
