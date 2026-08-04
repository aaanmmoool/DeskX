"""Step 3 — Results Page (Review + Processing).

Shows:
* Summary card: input file, output path, selected columns, pipeline
* "Process" button → triggers pipeline via BackgroundWorker
* Progress bar
* Status / result area
* Formatted report (not raw JSON)
"""

from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from deskx.core.config import SANITIZED_SUFFIX
from deskx.core.utils import build_output_filename, humanize_bytes
from deskx.processing.job import JobConfig
from deskx.processing.pipeline import TransformStep, TRANSFORM_INFO
from deskx.services.background_worker import BackgroundWorker
from deskx.services.progress import CompletionEvent, ErrorEvent, ProgressEvent


class ResultsPage(QWidget):
    """Review summary and processing — Step 3."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._source_path: Path | None = None
        self._output_folder: str = ""
        self._selected_columns: list[str] = []
        self._transform_steps: list[TransformStep] = []
        self._import_settings: dict = {}
        self._worker: BackgroundWorker | None = None
        self._setup_ui()

    # ── Public API ──────────────────────────────────────────────────

    def set_source(self, path: str) -> None:
        self._source_path = Path(path)
        self._refresh_summary()

    def set_output_folder(self, folder: str) -> None:
        self._output_folder = folder
        self._refresh_summary()

    def set_selected_columns(self, columns: list[str]) -> None:
        self._selected_columns = columns
        self._refresh_summary()

    def set_transform_pipeline(self, steps: list[TransformStep]) -> None:
        self._transform_steps = steps
        self._refresh_summary()

    def set_import_settings(self, settings: dict) -> None:
        self._import_settings = settings

    # ── Setup ───────────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 28, 32, 28)
        root.setSpacing(0)

        # ── Header ──────────────────────────────────────────────────
        heading = QLabel("Process & Results")
        heading.setProperty("role", "heading")
        root.addWidget(heading)

        subtitle = QLabel(
            "Review your configuration and process the file."
        )
        subtitle.setProperty("role", "subheading")
        subtitle.setContentsMargins(0, 4, 0, 0)
        root.addWidget(subtitle)

        root.addSpacing(20)

        # ── Summary card ────────────────────────────────────────────
        self._summary_card = QFrame()
        self._summary_card.setProperty("role", "card")
        summary_layout = QVBoxLayout(self._summary_card)
        summary_layout.setContentsMargins(20, 16, 20, 16)
        summary_layout.setSpacing(10)

        self._input_label = self._make_info_row(
            summary_layout, "Input File", "—"
        )
        self._output_label = self._make_info_row(
            summary_layout, "Output Path", "—"
        )
        self._columns_label = self._make_info_row(
            summary_layout, "Columns", "—"
        )
        self._pipeline_label = self._make_info_row(
            summary_layout, "Pipeline", "No transforms"
        )

        root.addWidget(self._summary_card)
        root.addSpacing(16)

        # ── Process button + cancel ─────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        self._process_btn = QPushButton("▶  Process")
        self._process_btn.setProperty("role", "primary")
        self._process_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._process_btn.setMinimumHeight(44)
        self._process_btn.setMinimumWidth(160)
        self._process_btn.clicked.connect(self._on_process)
        btn_row.addWidget(self._process_btn)

        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._cancel_btn.setMinimumHeight(44)
        self._cancel_btn.setEnabled(False)
        self._cancel_btn.clicked.connect(self._on_cancel)
        btn_row.addWidget(self._cancel_btn)

        btn_row.addStretch()
        root.addLayout(btn_row)

        root.addSpacing(12)

        # ── Progress bar ────────────────────────────────────────────
        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        self._progress.setTextVisible(False)
        root.addWidget(self._progress)

        root.addSpacing(6)

        self._status_label = QLabel("")
        self._status_label.setProperty("role", "caption")
        root.addWidget(self._status_label)

        root.addSpacing(16)

        # ── Results output ──────────────────────────────────────────
        results_label = QLabel("Report")
        results_label.setProperty("role", "subheading")
        root.addWidget(results_label)

        root.addSpacing(6)

        self._results_text = QTextEdit()
        self._results_text.setReadOnly(True)
        self._results_text.setPlaceholderText(
            "Processing report will appear here…"
        )
        self._results_text.setMinimumHeight(150)
        root.addWidget(self._results_text)

        root.addStretch()

    # ── Processing ──────────────────────────────────────────────────

    def _on_process(self) -> None:
        if not self._source_path:
            QMessageBox.warning(
                self, "No File", "Please upload a file first."
            )
            return

        # Build output path
        output_dir = (
            Path(self._output_folder)
            if self._output_folder
            else self._source_path.parent
        )
        output_name = build_output_filename(
            self._source_path, SANITIZED_SUFFIX
        )
        output_path = output_dir / output_name

        # Guard: don't overwrite
        if output_path.exists():
            reply = QMessageBox.question(
                self,
                "File Exists",
                f"'{output_name}' already exists in the output folder.\n\n"
                "Do you want to overwrite it?",
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        config = JobConfig(
            source_path=self._source_path,
            output_path=output_path,
            selected_columns=self._selected_columns,
            transform_steps=self._transform_steps,
            header_row=self._import_settings.get("header_row", 0),
            sheet_name=self._import_settings.get("sheet_name", 0),
            delimiter=self._import_settings.get("delimiter"),
        )

        self._set_processing_state(True)
        self._results_text.clear()

        self._worker = BackgroundWorker(config)
        self._worker.progress.connect(self._on_progress)
        self._worker.completed.connect(self._on_completed)
        self._worker.failed.connect(self._on_failed)
        self._worker.start()

    def _on_cancel(self) -> None:
        if self._worker:
            self._worker.cancel()

    # ── Worker signal handlers ──────────────────────────────────────

    def _on_progress(self, event: ProgressEvent) -> None:
        self._progress.setValue(event.percent)
        self._status_label.setText(event.message)

    def _on_completed(self, event: CompletionEvent) -> None:
        self._set_processing_state(False)
        self._progress.setValue(100)
        self._status_label.setText("✅  " + event.message)

        # Display formatted report
        try:
            report = json.loads(event.report_json)
            self._results_text.setPlainText(
                self._format_report(report)
            )
        except json.JSONDecodeError:
            self._results_text.setPlainText(event.report_json)

    def _on_failed(self, event: ErrorEvent) -> None:
        self._set_processing_state(False)
        icon = "⚠️" if event.is_cancellation else "❌"
        self._status_label.setText(f"{icon}  {event.message}")
        self._progress.setValue(0)

    # ── Helpers ─────────────────────────────────────────────────────

    def _set_processing_state(self, running: bool) -> None:
        self._process_btn.setEnabled(not running)
        self._cancel_btn.setEnabled(running)

    def _refresh_summary(self) -> None:
        if self._source_path:
            self._input_label.setText(str(self._source_path))

            output_dir = (
                self._output_folder
                if self._output_folder
                else str(self._source_path.parent)
            )
            output_name = build_output_filename(
                self._source_path, SANITIZED_SUFFIX
            )
            self._output_label.setText(
                str(Path(output_dir) / output_name)
            )
        else:
            self._input_label.setText("—")
            self._output_label.setText("—")

        if self._selected_columns:
            text = ", ".join(self._selected_columns[:8])
            if len(self._selected_columns) > 8:
                text += f"  (+{len(self._selected_columns) - 8} more)"
            self._columns_label.setText(text)
        else:
            self._columns_label.setText("All columns")

        if self._transform_steps:
            step_names = []
            for step in self._transform_steps[:5]:
                info = TRANSFORM_INFO.get(step.transform_type, {})
                step_names.append(info.get("name", "?"))
            text = " → ".join(step_names)
            if len(self._transform_steps) > 5:
                text += f" (+{len(self._transform_steps) - 5} more)"
            self._pipeline_label.setText(text)
        else:
            self._pipeline_label.setText("No transforms (safe copy)")

    def _format_report(self, report: dict) -> str:
        """Format the report dict as a human-readable string."""
        lines = []
        lines.append("═" * 50)
        lines.append("  PROCESSING REPORT")
        lines.append("═" * 50)
        lines.append("")

        status = report.get("status", "unknown")
        icon = {"success": "✅", "error": "❌", "cancelled": "⚠️"}.get(
            status, "❓"
        )
        lines.append(f"  Status:      {icon}  {status.upper()}")
        lines.append(f"  Duration:    {report.get('duration_seconds', 0):.2f}s")
        lines.append("")

        lines.append("  Input:       " + report.get("source_path", "—"))
        lines.append("  Output:      " + report.get("output_path", "—"))
        lines.append("")

        row_count = report.get("row_count")
        col_count = report.get("column_count")
        if row_count is not None:
            lines.append(f"  Rows:        {row_count:,}")
        if col_count is not None:
            lines.append(f"  Columns:     {col_count}")

        cols = report.get("columns_selected", [])
        if cols:
            lines.append(f"  Selected:    {len(cols)} columns")

        lines.append("")
        lines.append(f"  Source Hash: {report.get('source_hash', '—')[:16]}…")
        lines.append(f"  Output Hash: {report.get('output_hash', '—')[:16]}…")

        # Pipeline summary
        pipeline_summary = report.get("pipeline_summary")
        if pipeline_summary:
            lines.append("")
            lines.append("─" * 50)
            lines.append(pipeline_summary)

        error = report.get("error_message")
        if error:
            lines.append("")
            lines.append(f"  ❌ Error: {error}")

        lines.append("")
        lines.append("═" * 50)
        return "\n".join(lines)

    @staticmethod
    def _make_info_row(
        parent_layout: QVBoxLayout,
        label_text: str,
        value_text: str,
    ) -> QLabel:
        """Create a label + value row inside a card."""
        row = QHBoxLayout()
        row.setSpacing(12)

        label = QLabel(label_text)
        label.setProperty("role", "caption")
        label.setFixedWidth(100)
        row.addWidget(label)

        value = QLabel(value_text)
        value.setWordWrap(True)
        value.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        row.addWidget(value)

        parent_layout.addLayout(row)
        return value
