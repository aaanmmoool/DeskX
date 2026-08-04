"""Tests for processing.job module."""

from __future__ import annotations

import threading
from pathlib import Path

import pytest

from deskx.core.exceptions import CancellationError, ProcessingError
from deskx.processing.job import (
    JobConfig,
    JobStatus,
    ProcessingJob,
    ProgressUpdate,
)


class TestProcessingJob:
    def test_safe_copy_creates_output(
        self, sample_csv: Path, tmp_output_dir: Path
    ):
        output = tmp_output_dir / "out.csv"
        config = JobConfig(source_path=sample_csv, output_path=output)
        job = ProcessingJob(config=config)
        report = job.run()

        assert output.exists()
        assert output.read_bytes() == sample_csv.read_bytes()
        assert report.status == "success"
        assert job.status == JobStatus.COMPLETED

    def test_hashes_match_for_copy(
        self, sample_csv: Path, tmp_output_dir: Path
    ):
        output = tmp_output_dir / "out.csv"
        config = JobConfig(source_path=sample_csv, output_path=output)
        job = ProcessingJob(config=config)
        report = job.run()

        # For a safe copy, source and output should be identical
        assert report.source_hash == report.output_hash
        assert len(report.source_hash) == 64

    def test_same_path_raises(self, sample_csv: Path):
        config = JobConfig(
            source_path=sample_csv, output_path=sample_csv
        )
        job = ProcessingJob(config=config)
        with pytest.raises(ProcessingError):
            job.run()
        assert job.status == JobStatus.FAILED

    def test_missing_source_raises(self, tmp_path: Path):
        config = JobConfig(
            source_path=tmp_path / "ghost.csv",
            output_path=tmp_path / "out.csv",
        )
        job = ProcessingJob(config=config)
        with pytest.raises(ProcessingError):
            job.run()

    def test_progress_callback_invoked(
        self, sample_csv: Path, tmp_output_dir: Path
    ):
        output = tmp_output_dir / "out.csv"
        config = JobConfig(source_path=sample_csv, output_path=output)
        updates: list[ProgressUpdate] = []

        job = ProcessingJob(
            config=config, on_progress=updates.append
        )
        job.run()

        assert len(updates) > 0
        # First update should be validation
        assert updates[0].status == JobStatus.VALIDATING
        # Last update should be completed
        assert updates[-1].status == JobStatus.COMPLETED
        assert updates[-1].percent == 100

    def test_cancellation(
        self, sample_csv: Path, tmp_output_dir: Path
    ):
        output = tmp_output_dir / "out.csv"
        config = JobConfig(source_path=sample_csv, output_path=output)
        cancel = threading.Event()
        cancel.set()  # Pre-cancelled

        job = ProcessingJob(config=config, cancel_event=cancel)
        with pytest.raises(CancellationError):
            job.run()
        assert job.status == JobStatus.CANCELLED
        assert job.report is not None
        assert job.report.status == "cancelled"

    def test_report_always_generated(
        self, sample_csv: Path, tmp_output_dir: Path
    ):
        output = tmp_output_dir / "out.csv"
        config = JobConfig(
            source_path=sample_csv,
            output_path=output,
            selected_columns=["name", "email"],
        )
        job = ProcessingJob(config=config)
        report = job.run()

        assert report.columns_selected == ["name", "email"]
        assert report.started_at is not None
        assert report.finished_at is not None
