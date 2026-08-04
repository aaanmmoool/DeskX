"""Tests for processing.report_generator module."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from deskx.processing.report_generator import ReportGenerator


class TestReportGenerator:
    def test_build_creates_report(self):
        now = datetime.now(timezone.utc)
        report = ReportGenerator.build(
            source_path=Path("input.csv"),
            output_path=Path("output.csv"),
            source_hash="abc123",
            output_hash="def456",
            status="success",
            started_at=now,
            finished_at=now,
            row_count=100,
            column_count=5,
            columns_selected=["name", "email"],
        )
        assert report.status == "success"
        assert report.source_hash == "abc123"
        assert report.row_count == 100
        assert report.columns_selected == ["name", "email"]

    def test_to_dict(self):
        now = datetime.now(timezone.utc)
        report = ReportGenerator.build(
            source_path=Path("a.csv"),
            output_path=Path("b.csv"),
            source_hash="aaa",
            output_hash="bbb",
            status="success",
            started_at=now,
        )
        d = report.to_dict()
        assert isinstance(d, dict)
        assert d["status"] == "success"
        assert "source_path" in d

    def test_to_json(self):
        now = datetime.now(timezone.utc)
        report = ReportGenerator.build(
            source_path=Path("a.csv"),
            output_path=Path("b.csv"),
            source_hash="aaa",
            output_hash="bbb",
            status="error",
            started_at=now,
            error_message="Something broke",
        )
        j = report.to_json()
        parsed = json.loads(j)
        assert parsed["status"] == "error"
        assert parsed["error_message"] == "Something broke"

    def test_duration_calculated(self):
        t1 = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        t2 = datetime(2024, 1, 1, 0, 0, 5, tzinfo=timezone.utc)
        report = ReportGenerator.build(
            source_path=Path("a.csv"),
            output_path=Path("b.csv"),
            source_hash="",
            output_hash="",
            status="success",
            started_at=t1,
            finished_at=t2,
        )
        assert report.duration_seconds == 5.0

    def test_defaults(self):
        now = datetime.now(timezone.utc)
        report = ReportGenerator.build(
            source_path=Path("a.csv"),
            output_path=Path("b.csv"),
            source_hash="",
            output_hash="",
            status="success",
            started_at=now,
        )
        assert report.row_count is None
        assert report.column_count is None
        assert report.columns_selected == []
        assert report.error_message is None
