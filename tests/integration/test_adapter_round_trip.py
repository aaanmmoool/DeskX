"""Integration test — adapter round-trip (read → write → compare)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from deskx.adapters.csv_adapter import CsvAdapter
from deskx.adapters.json_adapter import JsonAdapter
from deskx.adapters.txt_adapter import TxtAdapter
from deskx.adapters.xlsx_adapter import XlsxAdapter


class TestAdapterRoundTrip:
    """Read a fixture → write it out → read it back → compare."""

    def test_csv_round_trip(self, sample_csv: Path, tmp_path: Path):
        adapter = CsvAdapter()
        df_original = adapter.read_full(sample_csv)

        out = tmp_path / "round.csv"
        adapter.write(df_original, out)
        df_reloaded = adapter.read_full(out)

        pd.testing.assert_frame_equal(df_reloaded, df_original)

    def test_json_round_trip(self, sample_json: Path, tmp_path: Path):
        adapter = JsonAdapter()
        df_original = adapter.read_full(sample_json)

        out = tmp_path / "round.json"
        adapter.write(df_original, out)
        df_reloaded = adapter.read_full(out)

        # Column order may differ in JSON
        assert set(df_reloaded.columns) == set(df_original.columns)
        assert len(df_reloaded) == len(df_original)

    def test_txt_round_trip(self, sample_txt: Path, tmp_path: Path):
        adapter = TxtAdapter()
        df_original = adapter.read_full(sample_txt)

        out = tmp_path / "round.txt"
        adapter.write(df_original, out)
        df_reloaded = adapter.read_full(out)

        assert set(df_reloaded.columns) == set(df_original.columns)
        assert len(df_reloaded) == len(df_original)

    def test_xlsx_round_trip(
        self, sample_df: pd.DataFrame, tmp_path: Path
    ):
        adapter = XlsxAdapter()

        out1 = tmp_path / "step1.xlsx"
        adapter.write(sample_df, out1)
        df_reloaded = adapter.read_full(out1)

        out2 = tmp_path / "step2.xlsx"
        adapter.write(df_reloaded, out2)
        df_final = adapter.read_full(out2)
        pd.testing.assert_frame_equal(df_final, sample_df, check_dtype=False)
