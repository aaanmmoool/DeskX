"""Results screen shown after a job finishes.

Every figure comes straight from the ``JobReport`` the processing
engine already produces.  Nothing here is estimated or invented: if
the report omits a value, the tile is hidden.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from deskx.core.utils import humanize_bytes, truncate_path
from deskx.gui.theme import ColorPalette, SIZE, SPACE, palette
from deskx.gui.theme.icons import Icon, get_pixmap, icon_label
from deskx.gui.widgets.components import (
    Badge,
    Button,
    Card,
    InfoNote,
    StatCard,
    StepIndicator,
    Themed,
    centered_page,
    label,
    scroll_container,
)
from deskx.gui.workflow import STEP_DONE, WORKFLOW_STEPS


class ResultsPage(QWidget, Themed):
    """Completion summary with follow-up actions.

    Signals
    -------
    open_report_requested()
        Show the full audit report.
    process_another_requested()
        Start over with a new file.
    """

    open_report_requested = Signal()
    process_another_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._report: dict = {}
        self._output_path: Path | None = None
        self._setup_ui()
        self._register_theme()

    # ── Public API ──────────────────────────────────────────────────

    def show_report(self, report: dict) -> None:
        """Populate the screen from a decoded ``JobReport``."""
        self._report = report or {}
        output = self._report.get("output_path", "")
        self._output_path = Path(output) if output else None

        if self._output_path is not None:
            self._filename.setText(self._output_path.name)
            self._filename.setToolTip(str(self._output_path))
            self._location.setText(truncate_path(self._output_path.parent, 58))
            self._location.setToolTip(str(self._output_path.parent))
            self._open_folder_btn.setEnabled(self._output_path.parent.is_dir())
            try:
                self._size_badge.setText(
                    humanize_bytes(self._output_path.stat().st_size)
                )
                self._size_badge.setVisible(True)
            except OSError:
                self._size_badge.setVisible(False)
        else:
            self._filename.setText("Output file")
            self._location.setText("")
            self._size_badge.setVisible(False)
            self._open_folder_btn.setEnabled(False)

        rows = self._report.get("row_count")
        self._rows_card.setVisible(rows is not None)
        if rows is not None:
            self._rows_card.set_value(f"{rows:,}", "written to the new file")

        columns = self._report.get("column_count")
        self._cols_card.setVisible(columns is not None)
        if columns is not None:
            self._cols_card.set_value(f"{columns:,}", "columns in the output")

        duration = self._report.get("duration_seconds")
        self._time_card.setVisible(duration is not None)
        if duration is not None:
            self._time_card.set_value(f"{float(duration):.2f}s", "total run time")

        source = self._report.get("source_path", "")
        self._source_note.set_message(
            f"Your original file is unchanged: {Path(source).name}"
            if source
            else "Your original file is unchanged.",
            "success",
        )

        self._steps_summary.setText(_steps_summary(self._report))

    # ── Setup ───────────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        column = QWidget()
        column.setObjectName("pageRoot")
        col = QVBoxLayout(column)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(SPACE.lg)

        steps = StepIndicator(WORKFLOW_STEPS)
        steps.set_current(STEP_DONE)
        col.addWidget(steps)

        col.addWidget(self._build_hero())

        stats = QHBoxLayout()
        stats.setSpacing(SPACE.lg)
        self._rows_card = StatCard("Rows processed", "—", Icon.TABLE, "primary")
        self._cols_card = StatCard("Columns written", "—", Icon.COLUMNS, "secondary")
        self._time_card = StatCard("Completed in", "—", Icon.CLOCK, "primary")
        stats.addWidget(self._rows_card)
        stats.addWidget(self._cols_card)
        stats.addWidget(self._time_card)
        col.addLayout(stats)

        col.addWidget(self._build_summary_card())
        col.addStretch()

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(scroll_container(centered_page(column, max_width=900)))

    def _build_hero(self) -> QWidget:
        card = Card(padding=SPACE.xxl, spacing=SPACE.lg, elevated=True)

        head = QHBoxLayout()
        head.setSpacing(SPACE.lg)

        self._tick = icon_label(Icon.SUCCESS, palette().success, 40, 1.7)
        head.addWidget(self._tick, 0, Qt.AlignmentFlag.AlignTop)

        col = QVBoxLayout()
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(SPACE.xs)
        col.addWidget(label("Your dataset is ready", "pageTitle"))

        name_row = QHBoxLayout()
        name_row.setContentsMargins(0, 0, 0, 0)
        name_row.setSpacing(SPACE.sm)
        self._filename = label("—", "cardTitle", tone="primary")
        name_row.addWidget(self._filename)
        self._size_badge = Badge("", "neutral")
        name_row.addWidget(self._size_badge)
        name_row.addStretch()
        col.addLayout(name_row)

        self._location = label("", "caption")
        col.addWidget(self._location)
        head.addLayout(col, 1)

        card.add_layout(head)

        self._source_note = InfoNote(
            "Your original file is unchanged.", variant="success", icon=Icon.SHIELD
        )
        card.add(self._source_note)

        actions = QHBoxLayout()
        actions.setSpacing(SPACE.sm)

        self._open_folder_btn = Button(
            "Open output folder",
            icon=Icon.FOLDER_OPEN,
            role="primary",
            height=SIZE.control_height_lg,
        )
        self._open_folder_btn.clicked.connect(self._open_output_folder)
        actions.addWidget(self._open_folder_btn)

        report_btn = Button(
            "View report", icon=Icon.REPORTS, height=SIZE.control_height_lg
        )
        report_btn.setToolTip("See the full audit report for this job")
        report_btn.clicked.connect(self.open_report_requested.emit)
        actions.addWidget(report_btn)

        another = Button(
            "Process another file",
            icon=Icon.UPLOAD,
            role="ghost",
            height=SIZE.control_height_lg,
        )
        another.clicked.connect(self.process_another_requested.emit)
        actions.addWidget(another)

        actions.addStretch()
        card.add_layout(actions)
        return card

    def _build_summary_card(self) -> QWidget:
        card = Card(padding=SPACE.xl, spacing=SPACE.sm)
        card.add(label("WHAT DESKX DID", "eyebrow"))
        self._steps_summary = label("", "body", wrap=True)
        card.add(self._steps_summary)
        return card

    # ── Actions ─────────────────────────────────────────────────────

    def _open_output_folder(self) -> None:
        """Reveal the output file in the system file manager."""
        if self._output_path is None:
            return
        folder = self._output_path.parent
        if not folder.is_dir():
            return

        if sys.platform == "win32":
            if self._output_path.is_file():
                subprocess.Popen(["explorer", "/select,", str(self._output_path)])
            else:
                subprocess.Popen(["explorer", str(folder)])
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(folder)])
        else:
            subprocess.Popen(["xdg-open", str(folder)])

    def apply_theme(self, p: ColorPalette) -> None:
        self._tick.setPixmap(get_pixmap(Icon.SUCCESS, p.success, 40, 1.7))


def _steps_summary(report: dict) -> str:
    """Describe the run using only values present in the report."""
    lines: list[str] = []

    summary = report.get("pipeline_summary")
    if summary:
        applied = [
            line.strip().lstrip("✓ ").split(":", 1)[-1].strip()
            for line in summary.splitlines()
            if line.strip().startswith("✓ Step")
        ]
        if applied:
            lines.append("Applied " + ", ".join(applied) + ".")

    selected = report.get("columns_selected") or []
    if selected:
        lines.append(f"Kept {len(selected)} selected column(s).")

    source_hash = report.get("source_hash", "")
    output_hash = report.get("output_hash", "")
    if source_hash and output_hash:
        lines.append(
            f"SHA-256 recorded for both files "
            f"(source {source_hash[:12]}…, output {output_hash[:12]}…)."
        )

    if not lines:
        lines.append("The file was copied safely with no changes applied.")

    return "  ".join(lines)
