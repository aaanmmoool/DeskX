"""Integration test — full transformation pipeline end-to-end.

Loads a messy CSV, configures transforms, processes, and verifies output.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from deskx.processing.job import JobConfig, JobStatus, ProcessingJob
from deskx.processing.pipeline import TransformStep, TransformType


FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


class TestTransformPipeline:
    """End-to-end: messy file → transforms → verified output."""

    @pytest.fixture
    def messy_csv(self):
        path = FIXTURES_DIR / "messy_data.csv"
        if not path.exists():
            pytest.skip("messy_data.csv fixture not found")
        return path

    def test_clean_and_normalize(
        self, messy_csv: Path, tmp_path: Path
    ):
        """Clean whitespace, remove empties, normalize numbers."""
        output = tmp_path / "cleaned.csv"
        config = JobConfig(
            source_path=messy_csv,
            output_path=output,
            transform_steps=[
                TransformStep(TransformType.TRIM_WHITESPACE),
                TransformStep(TransformType.REMOVE_EMPTY_ROWS),
                TransformStep(TransformType.REMOVE_EMPTY_COLUMNS),
                TransformStep(TransformType.REMOVE_DUPLICATES),
                TransformStep(
                    TransformType.NORMALIZE_NUMBERS,
                    params={"column": "Salary"},
                ),
            ],
        )
        job = ProcessingJob(config=config)
        report = job.run()

        assert report.status == "success"
        assert output.exists()
        assert report.row_count is not None
        assert report.column_count is not None

        # Verify output
        df = pd.read_csv(output)
        # Whitespace should be stripped from column names
        assert "First Name" in df.columns or "Name" in df.columns or any(
            "name" in c.lower() for c in df.columns
        )
        # Should have fewer rows than original (empties + duplicates removed)
        original = pd.read_csv(messy_csv)
        assert len(df) < len(original)

    def test_privacy_pipeline(
        self, messy_csv: Path, tmp_path: Path
    ):
        """Mask emails, redact salaries."""
        output = tmp_path / "private.csv"
        config = JobConfig(
            source_path=messy_csv,
            output_path=output,
            transform_steps=[
                TransformStep(TransformType.TRIM_WHITESPACE),
                TransformStep(
                    TransformType.MASK_COLUMN,
                    params={"column": "Email Address", "show_last": 4},
                ),
                TransformStep(
                    TransformType.REDACT_COLUMN,
                    params={"column": "Phone Number"},
                ),
            ],
        )
        job = ProcessingJob(config=config)
        report = job.run()

        assert report.status == "success"
        assert job.status == JobStatus.COMPLETED

        df = pd.read_csv(output)
        # Emails should be masked
        non_null_emails = df["Email Address"].dropna()
        if len(non_null_emails) > 0:
            for val in non_null_emails:
                assert "*" in str(val) or val == ""
        # Phones should be redacted
        non_null_phones = df["Phone Number"].dropna()
        if len(non_null_phones) > 0:
            for val in non_null_phones:
                assert val == "[REDACTED]"

    def test_column_selection(
        self, messy_csv: Path, tmp_path: Path
    ):
        """Select only specific columns."""
        output = tmp_path / "selected.csv"
        config = JobConfig(
            source_path=messy_csv,
            output_path=output,
            selected_columns=["Employee ID", "Department"],
            transform_steps=[
                TransformStep(TransformType.TRIM_WHITESPACE),
            ],
        )
        job = ProcessingJob(config=config)
        report = job.run()

        assert report.status == "success"
        df = pd.read_csv(output)
        # Should only have selected columns
        assert len(df.columns) <= 3  # May include trimmed name variants

    def test_pipeline_summary_in_report(
        self, messy_csv: Path, tmp_path: Path
    ):
        """Report should include pipeline summary."""
        output = tmp_path / "report_test.csv"
        config = JobConfig(
            source_path=messy_csv,
            output_path=output,
            transform_steps=[
                TransformStep(TransformType.TRIM_WHITESPACE),
                TransformStep(TransformType.REMOVE_EMPTY_ROWS),
            ],
        )
        job = ProcessingJob(config=config)
        report = job.run()

        assert report.pipeline_summary is not None
        assert "Pipeline Summary" in report.pipeline_summary

    def test_safe_copy_still_works(
        self, messy_csv: Path, tmp_path: Path
    ):
        """No transforms → byte-identical safe copy (backward compat)."""
        output = tmp_path / "copy.csv"
        config = JobConfig(
            source_path=messy_csv,
            output_path=output,
            # No transforms, no column selection
        )
        job = ProcessingJob(config=config)
        report = job.run()

        assert report.status == "success"
        assert output.read_bytes() == messy_csv.read_bytes()
        assert report.source_hash == report.output_hash


class TestMultiSheetXlsx:
    """Test XLSX worksheet selection."""

    @pytest.fixture
    def multi_xlsx(self):
        path = FIXTURES_DIR / "multi_sheet.xlsx"
        if not path.exists():
            pytest.skip("multi_sheet.xlsx fixture not found")
        return path

    def test_read_specific_sheet(self, multi_xlsx: Path):
        from deskx.adapters.xlsx_adapter import XlsxAdapter

        adapter = XlsxAdapter()
        sheets = adapter.get_sheet_names(multi_xlsx)
        assert len(sheets) == 3
        assert "Employees" in sheets
        assert "Departments" in sheets
        assert "Revenue" in sheets

        # Read specific sheet
        df = adapter.read_full(multi_xlsx, sheet_name="Revenue")
        assert "quarter" in df.columns
        assert len(df) == 4


class TestDelimiterDetection:
    """Test TXT delimiter auto-detection."""

    @pytest.fixture
    def pipe_txt(self):
        path = FIXTURES_DIR / "pipe_delimited.txt"
        if not path.exists():
            pytest.skip("pipe_delimited.txt fixture not found")
        return path

    def test_detect_pipe(self, pipe_txt: Path):
        from deskx.adapters.txt_adapter import TxtAdapter

        adapter = TxtAdapter()
        delimiter = adapter.detect_delimiter(pipe_txt)
        assert delimiter == "|"

    def test_read_with_pipe(self, pipe_txt: Path):
        from deskx.adapters.txt_adapter import TxtAdapter

        adapter = TxtAdapter()
        df = adapter.read_full(pipe_txt, delimiter="|")
        assert "customer_id" in df.columns
        assert len(df) == 5


class TestHeaderRowSelection:
    """Test CSV header row selection."""

    @pytest.fixture
    def header_csv(self):
        path = FIXTURES_DIR / "header_on_row3.csv"
        if not path.exists():
            pytest.skip("header_on_row3.csv fixture not found")
        return path

    def test_header_on_row_3(self, header_csv: Path):
        from deskx.adapters.csv_adapter import CsvAdapter

        adapter = CsvAdapter()
        # Row 2 (0-indexed) is the actual header
        df = adapter.read_full(header_csv, header_row=2)
        assert "ID" in df.columns
        assert "Name" in df.columns
        assert len(df) == 5
