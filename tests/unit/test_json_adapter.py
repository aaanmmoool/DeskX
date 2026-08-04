"""Tests for adapters.json_adapter module."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from deskx.adapters.json_adapter import JsonAdapter


class TestJsonAdapter:
    def setup_method(self):
        self.adapter = JsonAdapter()

    def test_extensions(self):
        assert ".json" in self.adapter.extensions

    def test_display_name(self):
        assert self.adapter.display_name == "JSON"

    def test_read_preview(self, sample_json: Path):
        df = self.adapter.read_preview(sample_json, max_rows=3)
        assert isinstance(df, pd.DataFrame)
        assert len(df) <= 3

    def test_read_full(self, sample_json: Path):
        df = self.adapter.read_full(sample_json)
        assert len(df) == 5
        assert "name" in df.columns

    def test_write(self, sample_df: pd.DataFrame, tmp_path: Path):
        out = tmp_path / "written.json"
        self.adapter.write(sample_df, out)
        assert out.exists()
        reloaded = pd.read_json(out)
        # JSON may reorder columns; compare sets
        assert set(reloaded.columns) == set(sample_df.columns)
        assert len(reloaded) == len(sample_df)

    def test_copy_file(self, sample_json: Path, tmp_path: Path):
        dest = tmp_path / "copy.json"
        self.adapter.copy_file(sample_json, dest)
        assert dest.exists()
        assert dest.read_bytes() == sample_json.read_bytes()
