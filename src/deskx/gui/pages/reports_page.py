"""Reports screen.

Renders the ``JobReport`` produced by the processing engine for the
most recent job — the integrity hashes, the pipeline summary, and the
raw JSON for anyone who needs the full audit trail.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QApplication,
    QGridLayout,
    QHBoxLayout,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from deskx.gui.theme import SIZE, SPACE
from deskx.gui.theme.icons import Icon
from deskx.gui.widgets.components import (
    Badge,
    Button,
    Card,
    EmptyState,
    SectionHeader,
    centered_page,
    clear_layout,
    label,
    scroll_container,
)

_FIELD_LABELS: list[tuple[str, str]] = [
    ("source_path", "Source file"),
    ("output_path", "Output file"),
    ("status", "Status"),
    ("started_at", "Started"),
    ("finished_at", "Finished"),
    ("duration_seconds", "Duration"),
    ("row_count", "Rows"),
    ("column_count", "Columns"),
    ("source_hash", "Source SHA-256"),
    ("output_hash", "Output SHA-256"),
]


class ReportsPage(QWidget):
    """Audit report for the last completed job.

    Signals
    -------
    copied(str)
        Emitted with a confirmation message after copying to clipboard.
    """

    copied = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._report: dict = {}
        self._report_json: str = ""
        self._setup_ui()
        self._apply_empty_state()

    # ── Public API ──────────────────────────────────────────────────

    def set_report(self, report: dict, report_json: str) -> None:
        """Show a decoded report and keep its raw JSON for copying."""
        self._report = report or {}
        self._report_json = report_json or ""

        has_report = bool(self._report)
        self._empty.setVisible(not has_report)
        self._content.setVisible(has_report)
        if not has_report:
            return

        status = str(self._report.get("status", "unknown"))
        self._status_badge.set_content(
            status.title(),
            {"success": "success", "cancelled": "warning"}.get(status, "error"),
        )

        output = self._report.get("output_path", "")
        self._title.setText(Path(output).name if output else "Processing report")

        self._fill_fields()
        self._pipeline_box.setPlainText(
            self._report.get("pipeline_summary")
            or "No transformations were applied — the file was copied as-is."
        )
        self._json_box.setPlainText(self._report_json)

    # ── Setup ───────────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        column = QWidget()
        column.setObjectName("pageRoot")
        col = QVBoxLayout(column)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(SPACE.lg)

        col.addWidget(label("Reports", "pageTitle"))
        col.addWidget(
            label(
                "DeskX records what it did to every file so the change can be "
                "verified later.",
                "subheading",
                wrap=True,
            )
        )

        self._empty = EmptyState(
            Icon.REPORTS,
            "No report yet",
            "Process a file and its audit report will appear here.",
        )
        col.addWidget(self._empty)

        self._content = QWidget()
        content_col = QVBoxLayout(self._content)
        content_col.setContentsMargins(0, 0, 0, 0)
        content_col.setSpacing(SPACE.lg)

        content_col.addWidget(self._build_summary_card())
        content_col.addWidget(self._build_pipeline_card())
        content_col.addWidget(self._build_json_card())
        col.addWidget(self._content)

        col.addStretch()

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(scroll_container(centered_page(column, max_width=940)))

    def _build_summary_card(self) -> QWidget:
        card = Card(padding=SPACE.xl, spacing=SPACE.md)

        head = QHBoxLayout()
        head.setSpacing(SPACE.sm)
        self._title = label("Processing report", "sectionTitle")
        head.addWidget(self._title)
        self._status_badge = Badge("", "neutral")
        head.addWidget(self._status_badge)
        head.addStretch()
        card.add_layout(head)

        grid_host = QWidget()
        self._grid = QGridLayout(grid_host)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setHorizontalSpacing(SPACE.xl)
        self._grid.setVerticalSpacing(SPACE.sm)
        self._grid.setColumnStretch(1, 1)
        self._grid.setColumnStretch(3, 1)
        card.add(grid_host)
        return card

    def _build_pipeline_card(self) -> QWidget:
        card = Card(padding=SPACE.xl, spacing=SPACE.md)
        card.add(SectionHeader("Pipeline summary", Icon.PIPELINE))
        self._pipeline_box = QTextEdit()
        self._pipeline_box.setReadOnly(True)
        self._pipeline_box.setMinimumHeight(150)
        card.add(self._pipeline_box)
        return card

    def _build_json_card(self) -> QWidget:
        card = Card(padding=SPACE.xl, spacing=SPACE.md)

        header = SectionHeader(
            "Full report",
            Icon.REPORTS,
            "The complete machine-readable audit record.",
        )
        copy_btn = Button("Copy JSON", icon=Icon.COPY, role="ghost")
        copy_btn.setToolTip("Copy the report to the clipboard")
        copy_btn.clicked.connect(self._copy_json)
        header.add_trailing(copy_btn)
        card.add(header)

        self._json_box = QTextEdit()
        self._json_box.setReadOnly(True)
        self._json_box.setMinimumHeight(220)
        card.add(self._json_box)
        return card

    def _fill_fields(self) -> None:
        clear_layout(self._grid)

        row = 0
        column = 0
        for key, caption in _FIELD_LABELS:
            value = self._report.get(key)
            if value in (None, ""):
                continue

            text = _format_value(key, value)
            self._grid.addWidget(
                label(caption.upper(), "eyebrow"),
                row,
                column * 2,
                1,
                1,
                Qt.AlignmentFlag.AlignTop,
            )
            value_lbl = label(
                text, "mono" if key.endswith("hash") else "body", wrap=True
            )
            value_lbl.setToolTip(str(value))
            self._grid.addWidget(value_lbl, row, column * 2 + 1)

            column += 1
            if column > 1:
                column = 0
                row += 1

    def _apply_empty_state(self) -> None:
        self._content.setVisible(False)
        self._empty.setVisible(True)

    def _copy_json(self) -> None:
        if not self._report_json:
            return
        QApplication.clipboard().setText(self._report_json)
        self.copied.emit("Report copied to clipboard")


def _format_value(key: str, value) -> str:
    """Render a report field for display."""
    if key == "duration_seconds":
        return f"{float(value):.3f} seconds"
    if key in {"row_count", "column_count"}:
        return f"{int(value):,}"
    if key.endswith("hash"):
        # A 64-character digest has nowhere to wrap; the full value is
        # in the tooltip and in the copyable JSON below.
        text = str(value)
        return f"{text[:20]}…{text[-8:]}" if len(text) > 32 else text
    if key in {"source_path", "output_path"}:
        return str(value)
    if key.endswith("_at"):
        return str(value).replace("T", "  ").split("+")[0]
    return str(value)
