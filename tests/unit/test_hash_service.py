"""Tests for processing.hash_service module."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from deskx.processing.hash_service import HashService


class TestHashService:
    def test_compute_returns_hex_digest(self, sample_csv: Path):
        svc = HashService()
        result = svc.compute(sample_csv)
        assert isinstance(result, str)
        assert len(result) == 64  # SHA-256 hex length

    def test_compute_matches_stdlib(self, sample_csv: Path):
        svc = HashService()
        result = svc.compute(sample_csv)

        expected = hashlib.sha256(sample_csv.read_bytes()).hexdigest()
        assert result == expected

    def test_compute_deterministic(self, sample_csv: Path):
        svc = HashService()
        assert svc.compute(sample_csv) == svc.compute(sample_csv)

    def test_verify_true_for_correct_hash(self, sample_csv: Path):
        svc = HashService()
        h = svc.compute(sample_csv)
        assert svc.verify(sample_csv, h) is True

    def test_verify_false_for_wrong_hash(self, sample_csv: Path):
        svc = HashService()
        assert svc.verify(sample_csv, "0" * 64) is False

    def test_compute_file_not_found(self, tmp_path: Path):
        svc = HashService()
        with pytest.raises(FileNotFoundError):
            svc.compute(tmp_path / "nonexistent.csv")

    def test_different_files_different_hashes(
        self, sample_csv: Path, sample_json: Path
    ):
        svc = HashService()
        assert svc.compute(sample_csv) != svc.compute(sample_json)

    def test_custom_buffer_size(self, sample_csv: Path):
        svc = HashService(buffer_size=16)
        result = svc.compute(sample_csv)
        assert len(result) == 64
