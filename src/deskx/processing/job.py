"""Processing job orchestrator.

``ProcessingJob`` coordinates the full transformation pipeline:

1. Validate paths
2. Hash source file
3. Read source data via adapter
4. Apply column filtering
5. Execute transformation pipeline
6. Write output via adapter
7. Optionally strip XLSX metadata
8. Validate output
9. Hash output
10. Generate report

It accepts injected services (hash, validation, temp-file, report) so
every piece can be unit-tested in isolation.

This module has **no PySide6 dependency**.  Communication with the GUI
layer happens through the callback ``on_progress`` which accepts plain
``ProgressEvent`` dataclasses defined in ``services.progress``.
"""

from __future__ import annotations

import logging
import shutil
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable

import pandas as pd

from deskx.adapters.adapter_registry import AdapterRegistry, create_default_registry
from deskx.core.exceptions import CancellationError, ProcessingError
from deskx.processing.hash_service import HashService
from deskx.processing.pipeline import (
    PipelineResult,
    TransformStep,
    execute_pipeline,
)
from deskx.processing.report_generator import JobReport, ReportGenerator
from deskx.processing.temp_file_manager import TempFileManager
from deskx.processing.validation_service import ValidationService

logger = logging.getLogger(__name__)


# ── Job status ──────────────────────────────────────────────────────

class JobStatus(Enum):
    """Lifecycle states for a processing job."""

    PENDING = auto()
    VALIDATING = auto()
    HASHING_SOURCE = auto()
    READING = auto()
    PROCESSING = auto()
    WRITING = auto()
    VALIDATING_OUTPUT = auto()
    HASHING_OUTPUT = auto()
    GENERATING_REPORT = auto()
    COMPLETED = auto()
    CANCELLED = auto()
    FAILED = auto()


# ── Progress callback type ──────────────────────────────────────────

@dataclass(frozen=True)
class ProgressUpdate:
    """Lightweight progress payload — no Qt types."""

    status: JobStatus
    message: str
    percent: int = 0  # 0–100


ProgressCallback = Callable[[ProgressUpdate], None]


# ── Job configuration ──────────────────────────────────────────────

@dataclass
class JobConfig:
    """Inputs required to run a processing job."""

    source_path: Path
    output_path: Path
    selected_columns: list[str] = field(default_factory=list)
    transform_steps: list[TransformStep] = field(default_factory=list)
    strip_metadata: bool = False

    # Import settings
    header_row: int | None = 0  # 0 = first row, None = no header
    sheet_name: str | int = 0  # For XLSX files
    delimiter: str | None = None  # For TXT files (None = auto-detect)


# ── Processing job ──────────────────────────────────────────────────

class ProcessingJob:
    """Orchestrates the full transformation pipeline.

    Parameters
    ----------
    config
        Input/output paths, column selections, and transform steps.
    hash_service
        Injected hash computer.
    validation_service
        Injected path / output validator.
    registry
        Adapter registry for reading/writing files.
    on_progress
        Optional callback invoked at each stage transition.
    cancel_event
        A ``threading.Event`` that, when set, aborts the job.
    """

    def __init__(
        self,
        config: JobConfig,
        hash_service: HashService | None = None,
        validation_service: ValidationService | None = None,
        registry: AdapterRegistry | None = None,
        on_progress: ProgressCallback | None = None,
        cancel_event: threading.Event | None = None,
    ) -> None:
        self._config = config
        self._hash = hash_service or HashService()
        self._validation = validation_service or ValidationService()
        self._registry = registry or create_default_registry()
        self._on_progress = on_progress or (lambda _: None)
        self._cancel = cancel_event or threading.Event()

        self._status = JobStatus.PENDING
        self._source_hash = ""
        self._output_hash = ""
        self._started_at: datetime | None = None
        self._finished_at: datetime | None = None
        self._report: JobReport | None = None
        self._pipeline_result: PipelineResult | None = None

    # ── Properties ──────────────────────────────────────────────────

    @property
    def status(self) -> JobStatus:
        return self._status

    @property
    def report(self) -> JobReport | None:
        return self._report

    @property
    def config(self) -> JobConfig:
        return self._config

    @property
    def pipeline_result(self) -> PipelineResult | None:
        return self._pipeline_result

    # ── Execution ───────────────────────────────────────────────────

    def run(self) -> JobReport:
        """Execute the full pipeline.  Returns a :class:`JobReport`.

        Raises
        ------
        CancellationError
            If the cancel event is set during processing.
        ProcessingError
            For any non-cancellation failure.
        """
        self._started_at = datetime.now(timezone.utc)
        error_message: str | None = None
        row_count: int | None = None
        column_count: int | None = None
        pipeline_summary: str | None = None

        try:
            # ── Step 1: Validate paths ──────────────────────────
            self._set_status(JobStatus.VALIDATING, "Validating paths…", 5)
            self._check_cancelled()
            self._validation.validate_source_exists(self._config.source_path)
            self._validation.validate_paths(
                self._config.source_path,
                self._config.output_path,
            )

            # ── Step 2: Hash source file ────────────────────────
            self._set_status(
                JobStatus.HASHING_SOURCE, "Hashing source file…", 10
            )
            self._check_cancelled()
            self._source_hash = self._hash.compute(self._config.source_path)

            # ── Step 3: Read source data ────────────────────────
            self._set_status(JobStatus.READING, "Reading source file…", 20)
            self._check_cancelled()

            has_transforms = bool(self._config.transform_steps) or bool(
                self._config.selected_columns
            )

            if has_transforms:
                df = self._read_source()
                row_count = len(df)
                column_count = len(df.columns)

                # ── Step 4: Apply column selection ──────────────
                self._set_status(
                    JobStatus.PROCESSING, "Applying transformations…", 35
                )
                self._check_cancelled()

                if self._config.selected_columns:
                    # Only keep selected columns
                    valid_cols = [
                        c for c in self._config.selected_columns
                        if c in df.columns
                    ]
                    if valid_cols:
                        df = df[valid_cols]

                # ── Step 5: Execute pipeline ────────────────────
                if self._config.transform_steps:
                    self._set_status(
                        JobStatus.PROCESSING,
                        "Running transformation pipeline…",
                        50,
                    )
                    self._check_cancelled()
                    df, self._pipeline_result = execute_pipeline(
                        df, self._config.transform_steps
                    )
                    pipeline_summary = self._pipeline_result.summary_text()

                row_count = len(df)
                column_count = len(df.columns)

                # ── Step 6: Write output ────────────────────────
                self._set_status(
                    JobStatus.WRITING, "Writing output file…", 65
                )
                self._check_cancelled()
                self._write_output(df)
            else:
                # No transforms — safe copy
                self._set_status(
                    JobStatus.PROCESSING, "Copying file…", 40
                )
                self._check_cancelled()
                self._safe_copy()

            # ── Step 7: Strip metadata if requested ─────────────
            if (
                self._config.strip_metadata
                and self._config.output_path.suffix.lower() == ".xlsx"
            ):
                self._set_status(
                    JobStatus.PROCESSING,
                    "Stripping metadata…",
                    72,
                )
                from deskx.processing.transforms import strip_metadata_from_xlsx
                strip_metadata_from_xlsx(str(self._config.output_path))

            # ── Step 8: Validate output ─────────────────────────
            self._set_status(
                JobStatus.VALIDATING_OUTPUT, "Validating output…", 80
            )
            self._check_cancelled()
            self._validation.validate_output_exists(self._config.output_path)
            self._validation.validate_output_non_empty(
                self._config.output_path
            )

            # ── Step 9: Hash output ─────────────────────────────
            self._set_status(
                JobStatus.HASHING_OUTPUT, "Hashing output file…", 90
            )
            self._check_cancelled()
            self._output_hash = self._hash.compute(self._config.output_path)

            # ── Step 10: Generate report ────────────────────────
            self._set_status(
                JobStatus.GENERATING_REPORT, "Generating report…", 95
            )
            final_status = "success"

        except CancellationError:
            final_status = "cancelled"
            self._status = JobStatus.CANCELLED
            error_message = "Job cancelled by user."
            logger.info("Job cancelled.")
            raise

        except Exception as exc:
            final_status = "error"
            self._status = JobStatus.FAILED
            error_message = str(exc)
            logger.exception("Job failed: %s", exc)
            raise ProcessingError(str(exc)) from exc

        finally:
            self._finished_at = datetime.now(timezone.utc)
            self._report = ReportGenerator.build(
                source_path=self._config.source_path,
                output_path=self._config.output_path,
                source_hash=self._source_hash,
                output_hash=self._output_hash,
                status=final_status,
                started_at=self._started_at,
                finished_at=self._finished_at,
                row_count=row_count,
                column_count=column_count,
                columns_selected=self._config.selected_columns,
                error_message=error_message,
                pipeline_summary=pipeline_summary,
            )

        self._set_status(JobStatus.COMPLETED, "Done.", 100)
        return self._report

    # ── Internal helpers ────────────────────────────────────────────

    def _read_source(self) -> pd.DataFrame:
        """Read the source file via the appropriate adapter."""
        adapter = self._registry.get(self._config.source_path.suffix)

        # Honour the import options already carried on JobConfig so GUI
        # and CLI share one read path through the existing adapters.
        kwargs: dict[str, Any] = {
            "sheet_name": self._config.sheet_name,
        }
        if self._config.header_row is not None:
            kwargs["header_row"] = self._config.header_row
        if self._config.delimiter is not None:
            kwargs["delimiter"] = self._config.delimiter

        return adapter.read_full(self._config.source_path, **kwargs)

    def _write_output(self, df: pd.DataFrame) -> None:
        """Write transformed data through a temp file."""
        adapter = self._registry.get(self._config.output_path.suffix)
        with TempFileManager(self._config.output_path) as tmp:
            adapter.write(df, tmp.temp_path)

    def _safe_copy(self) -> None:
        """Copy the source file through a temp file (no transforms)."""
        with TempFileManager(self._config.output_path) as tmp:
            shutil.copy2(self._config.source_path, tmp.temp_path)

    def _set_status(
        self, status: JobStatus, message: str, percent: int
    ) -> None:
        self._status = status
        self._on_progress(ProgressUpdate(status, message, percent))

    def _check_cancelled(self) -> None:
        if self._cancel.is_set():
            raise CancellationError("Job cancelled by user.")
