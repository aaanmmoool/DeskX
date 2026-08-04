"""Tests for processing.temp_file_manager module."""

from __future__ import annotations

from pathlib import Path

import pytest

from deskx.core.config import TEMP_FILE_PREFIX
from deskx.processing.temp_file_manager import TempFileManager


class TestTempFileManager:
    def test_temp_path_in_same_directory(self, tmp_path: Path):
        final = tmp_path / "output.csv"
        with TempFileManager(final) as tmp:
            assert tmp.temp_path.parent == final.parent

    def test_temp_path_has_prefix(self, tmp_path: Path):
        final = tmp_path / "output.csv"
        with TempFileManager(final) as tmp:
            assert tmp.temp_path.name.startswith(TEMP_FILE_PREFIX)

    def test_success_promotes_temp_to_final(self, tmp_path: Path):
        final = tmp_path / "output.csv"
        with TempFileManager(final) as tmp:
            tmp.temp_path.write_text("hello")
        assert final.exists()
        assert final.read_text() == "hello"
        assert not tmp.temp_path.exists()

    def test_failure_cleans_up_temp(self, tmp_path: Path):
        final = tmp_path / "output.csv"
        temp_path = None
        with pytest.raises(ValueError):
            with TempFileManager(final) as tmp:
                tmp.temp_path.write_text("partial")
                temp_path = tmp.temp_path
                raise ValueError("Simulated failure")
        assert not final.exists()
        assert not temp_path.exists()

    def test_stale_temp_removed(self, tmp_path: Path):
        final = tmp_path / "output.csv"
        mgr = TempFileManager(final)
        # Create a stale temp file
        mgr.temp_path.write_text("stale")
        assert mgr.temp_path.exists()
        with mgr as tmp:
            # Stale file should be removed on __enter__
            tmp.temp_path.write_text("fresh")
        assert final.read_text() == "fresh"

    def test_final_path_property(self, tmp_path: Path):
        final = tmp_path / "output.csv"
        mgr = TempFileManager(final)
        assert mgr.final_path == final
