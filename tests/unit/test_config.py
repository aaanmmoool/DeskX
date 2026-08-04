"""Tests for core.config module."""

from __future__ import annotations

from pathlib import Path

from deskx.core.config import (
    APP_NAME,
    APP_VERSION,
    HASH_ALGORITHM,
    MAX_PREVIEW_ROWS,
    MAX_RECENT_FILES,
    SUPPORTED_EXTENSIONS,
    get_app_data_dir,
    get_recent_files_path,
)


class TestConfigConstants:
    def test_app_name_is_set(self):
        assert APP_NAME == "DeskX"

    def test_version_format(self):
        parts = APP_VERSION.split(".")
        assert len(parts) == 3
        assert all(p.isdigit() for p in parts)

    def test_supported_extensions(self):
        assert ".csv" in SUPPORTED_EXTENSIONS
        assert ".xlsx" in SUPPORTED_EXTENSIONS
        assert ".json" in SUPPORTED_EXTENSIONS
        assert ".txt" in SUPPORTED_EXTENSIONS
        assert len(SUPPORTED_EXTENSIONS) == 4

    def test_extensions_are_lowercase(self):
        for ext in SUPPORTED_EXTENSIONS:
            assert ext == ext.lower()
            assert ext.startswith(".")

    def test_preview_rows_positive(self):
        assert MAX_PREVIEW_ROWS > 0

    def test_recent_files_positive(self):
        assert MAX_RECENT_FILES > 0

    def test_hash_algorithm(self):
        assert HASH_ALGORITHM == "sha256"


class TestConfigPaths:
    def test_app_data_dir_exists(self):
        path = get_app_data_dir()
        assert path.exists()
        assert path.is_dir()

    def test_recent_files_path_is_json(self):
        path = get_recent_files_path()
        assert path.suffix == ".json"
        assert path.parent.exists()
