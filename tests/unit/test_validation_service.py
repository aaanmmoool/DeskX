"""Tests for processing.validation_service module."""

from __future__ import annotations

from pathlib import Path

import pytest

from deskx.core.exceptions import (
    OutputDirectoryError,
    SamePathError,
    ValidationError,
)
from deskx.processing.validation_service import ValidationService


class TestValidatePaths:
    def test_same_path_raises(self, sample_csv: Path):
        svc = ValidationService()
        with pytest.raises(SamePathError):
            svc.validate_paths(sample_csv, sample_csv)

    def test_resolved_same_path_raises(self, sample_csv: Path):
        svc = ValidationService()
        # Create an equivalent path with ".."
        alt = sample_csv.parent / ".." / sample_csv.parent.name / sample_csv.name
        with pytest.raises(SamePathError):
            svc.validate_paths(sample_csv, alt)

    def test_different_paths_pass(
        self, sample_csv: Path, tmp_output_dir: Path
    ):
        svc = ValidationService()
        output = tmp_output_dir / "out.csv"
        svc.validate_paths(sample_csv, output)  # Should not raise

    def test_missing_output_dir_raises(self, sample_csv: Path, tmp_path: Path):
        svc = ValidationService()
        output = tmp_path / "nonexistent_dir" / "out.csv"
        with pytest.raises(OutputDirectoryError):
            svc.validate_paths(sample_csv, output)


class TestValidateSourceExists:
    def test_existing_file_passes(self, sample_csv: Path):
        svc = ValidationService()
        svc.validate_source_exists(sample_csv)  # Should not raise

    def test_missing_file_raises(self, tmp_path: Path):
        svc = ValidationService()
        with pytest.raises(ValidationError, match="does not exist"):
            svc.validate_source_exists(tmp_path / "ghost.csv")


class TestValidateOutput:
    def test_output_exists_passes(self, sample_csv: Path):
        svc = ValidationService()
        svc.validate_output_exists(sample_csv)  # Should not raise

    def test_output_missing_raises(self, tmp_path: Path):
        svc = ValidationService()
        with pytest.raises(ValidationError, match="not created"):
            svc.validate_output_exists(tmp_path / "missing.csv")

    def test_output_empty_raises(self, tmp_path: Path):
        svc = ValidationService()
        empty = tmp_path / "empty.csv"
        empty.write_text("")
        with pytest.raises(ValidationError, match="empty"):
            svc.validate_output_non_empty(empty)

    def test_output_non_empty_passes(self, sample_csv: Path):
        svc = ValidationService()
        svc.validate_output_non_empty(sample_csv)  # Should not raise
