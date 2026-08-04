"""Integration test — full safe-copy pipeline end-to-end."""

from __future__ import annotations

from pathlib import Path

import pytest

from deskx.processing.hash_service import HashService
from deskx.processing.job import JobConfig, JobStatus, ProcessingJob


class TestFullCopyPipeline:
    """Runs the complete pipeline: validate → hash → copy → validate → hash."""

    @pytest.mark.parametrize(
        "fixture_name",
        ["sample_csv", "sample_json", "sample_txt"],
    )
    def test_copy_preserves_content(
        self,
        fixture_name: str,
        tmp_output_dir: Path,
        request: pytest.FixtureRequest,
    ):
        source: Path = request.getfixturevalue(fixture_name)
        output = tmp_output_dir / f"copy{source.suffix}"

        config = JobConfig(source_path=source, output_path=output)
        job = ProcessingJob(config=config)
        report = job.run()

        # Output file exists and matches source byte-for-byte
        assert output.exists()
        assert output.read_bytes() == source.read_bytes()
        assert report.status == "success"
        assert job.status == JobStatus.COMPLETED

    def test_source_not_modified(
        self, sample_csv: Path, tmp_output_dir: Path
    ):
        """Verify the original file is never changed."""
        hash_svc = HashService()
        before = hash_svc.compute(sample_csv)

        output = tmp_output_dir / "safe.csv"
        config = JobConfig(source_path=sample_csv, output_path=output)
        job = ProcessingJob(config=config)
        job.run()

        after = hash_svc.compute(sample_csv)
        assert before == after, "Source file was modified!"

    def test_report_contains_matching_hashes(
        self, sample_csv: Path, tmp_output_dir: Path
    ):
        output = tmp_output_dir / "hashed.csv"
        config = JobConfig(source_path=sample_csv, output_path=output)
        job = ProcessingJob(config=config)
        report = job.run()

        # For a pure copy, hashes must match
        assert report.source_hash == report.output_hash
        assert len(report.source_hash) == 64
