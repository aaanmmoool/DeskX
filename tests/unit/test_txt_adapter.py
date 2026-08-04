"""Tests for adapters.txt_adapter module."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from deskx.adapters.txt_adapter import TxtAdapter


class TestTxtAdapter:
    def setup_method(self):
        self.adapter = TxtAdapter()

    def test_extensions(self):
        assert ".txt" in self.adapter.extensions

    def test_display_name(self):
        assert "TXT" in self.adapter.display_name

    def test_read_preview(self, sample_txt: Path):
        df = self.adapter.read_preview(sample_txt, max_rows=3)
        assert isinstance(df, pd.DataFrame)
        assert len(df) <= 3

    def test_read_full(self, sample_txt: Path):
        df = self.adapter.read_full(sample_txt)
        assert len(df) == 5
        assert "name" in df.columns

    def test_write_and_reload(
        self, sample_df: pd.DataFrame, tmp_path: Path
    ):
        out = tmp_path / "written.txt"
        self.adapter.write(sample_df, out)
        assert out.exists()
        reloaded = self.adapter.read_full(out)
        assert len(reloaded) == len(sample_df)
        assert set(reloaded.columns) == set(sample_df.columns)

    def test_copy_file(self, sample_txt: Path, tmp_path: Path):
        dest = tmp_path / "copy.txt"
        self.adapter.copy_file(sample_txt, dest)
        assert dest.exists()
        assert dest.read_bytes() == sample_txt.read_bytes()
