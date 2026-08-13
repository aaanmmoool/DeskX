"""Processing screen.

Shows what the background worker is doing right now.  Every value on
this screen comes from the existing ``ProgressEvent`` stream — the
worker itself is untouched.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

from deskx.gui.theme import ColorPalette, SIZE, SPACE, palette
from deskx.gui.theme.icons import Icon, get_pixmap, icon_label
from deskx.gui.widgets.components import (
    Badge,
    Button,
    Card,
    InfoNote,
    StepIndicator,
    Themed,
    centered_page,
    label,
)
from deskx.gui.workflow import STEP_PROCESS, WORKFLOW_STEPS


class ProcessingPage(QWidget, Themed):
    """Live progress for the running job.

    Signals
    -------
    cancel_requested()
        The user pressed Cancel.
    """

    cancel_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._step_lines: list[str] = []
        self._setup_ui()
        self._register_theme()

    # ── Public API ──────────────────────────────────────────────────

    def start(
        self,
        source_path: Path,
        output_path: Path,
        step_count: int,
    ) -> None:
        """Reset the screen for a new job."""
        self._step_lines.clear()
        self._source_lbl.setText(source_path.name)
        self._source_lbl.setToolTip(str(source_path))
        self._output_lbl.setText(output_path.name)
        self._output_lbl.setToolTip(str(output_path))
        self._steps_badge.setText(
            f"{step_count} transformation{'s' if step_count != 1 else ''}"
        )
        self._progress.setValue(0)
        self._percent_lbl.setText("0%")
        self._stage_lbl.setText("Starting…")
        self._log_lbl.setText("")
        self._note.set_message(
            "Your original file is open read-only and will not be changed.",
            "info",
        )
        self._cancel_btn.setEnabled(True)
        self._cancel_btn.setText("Cancel")

    def update_progress(self, percent: int, message: str) -> None:
        """Reflect one ``ProgressEvent`` from the worker."""
        self._progress.setValue(percent)
        self._percent_lbl.setText(f"{percent}%")
        self._stage_lbl.setText(message)

        if message and (not self._step_lines or self._step_lines[-1] != message):
            self._step_lines.append(message)
            self._log_lbl.setText("\n".join(self._step_lines[-6:]))

    def mark_cancelling(self) -> None:
        self._cancel_btn.setEnabled(False)
        self._cancel_btn.setText("Cancelling…")
        self._stage_lbl.setText("Stopping safely…")
        self._note.set_message(
            "Finishing the current step, then cleaning up the temporary file.",
            "warning",
        )

    # ── Setup ───────────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        column = QWidget()
        column.setObjectName("pageRoot")
        col = QVBoxLayout(column)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(SPACE.lg)

        steps = StepIndicator(WORKFLOW_STEPS)
        steps.set_current(STEP_PROCESS)
        col.addWidget(steps)

        col.addWidget(label("Processing your dataset", "pageTitle"))
        col.addWidget(
            label(
                "DeskX is writing to a temporary file and will only publish the "
                "result once every step succeeds.",
                "subheading",
                wrap=True,
            )
        )

        card = Card(padding=SPACE.xxl, spacing=SPACE.lg, elevated=True)

        files = QHBoxLayout()
        files.setSpacing(SPACE.lg)
        files.addWidget(self._build_file_block("READING", Icon.FILE, "source"))
        self._arrow = icon_label(Icon.ARROW_RIGHT, palette().text_tertiary, SIZE.icon_lg)
        files.addWidget(self._arrow, 0, Qt.AlignmentFlag.AlignVCenter)
        files.addWidget(self._build_file_block("WRITING", Icon.DOWNLOAD, "output"))
        files.addStretch()
        card.add_layout(files)

        stage_row = QHBoxLayout()
        stage_row.setSpacing(SPACE.sm)
        self._stage_lbl = label("Starting…", "cardTitle")
        stage_row.addWidget(self._stage_lbl)
        stage_row.addStretch()
        self._steps_badge = Badge("", "primary")
        stage_row.addWidget(self._steps_badge)
        self._percent_lbl = label("0%", "cardTitle", tone="primary")
        stage_row.addWidget(self._percent_lbl)
        card.add_layout(stage_row)

        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setTextVisible(False)
        self._progress.setProperty("role", "thick")
        card.add(self._progress)

        self._log_lbl = label("", "caption", wrap=True)
        self._log_lbl.setMinimumHeight(84)
        self._log_lbl.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft
        )
        card.add(self._log_lbl)

        self._note = InfoNote(
            "Your original file is open read-only and will not be changed.",
            variant="info",
            icon=Icon.SHIELD,
        )
        card.add(self._note)

        actions = QHBoxLayout()
        actions.addStretch()
        self._cancel_btn = Button("Cancel", icon=Icon.CLOSE, role="ghost")
        self._cancel_btn.clicked.connect(self.cancel_requested.emit)
        actions.addWidget(self._cancel_btn)
        card.add_layout(actions)

        col.addWidget(card)
        col.addStretch()

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(centered_page(column, max_width=820))

    def _build_file_block(self, eyebrow: str, icon: str, kind: str) -> QWidget:
        block = QWidget()
        row = QHBoxLayout(block)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(SPACE.sm)

        glyph = icon_label(icon, palette().primary, SIZE.icon_lg)
        row.addWidget(glyph, 0, Qt.AlignmentFlag.AlignVCenter)

        col = QVBoxLayout()
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(0)
        col.addWidget(label(eyebrow, "eyebrow"))
        name = label("—", "body")
        col.addWidget(name)
        row.addLayout(col)

        if kind == "source":
            self._source_lbl = name
            self._source_icon = glyph
        else:
            self._output_lbl = name
            self._output_icon = glyph
        return block

    def apply_theme(self, p: ColorPalette) -> None:
        self._source_icon.setPixmap(get_pixmap(Icon.FILE, p.primary, SIZE.icon_lg))
        self._output_icon.setPixmap(get_pixmap(Icon.DOWNLOAD, p.primary, SIZE.icon_lg))
        self._arrow.setPixmap(
            get_pixmap(Icon.ARROW_RIGHT, p.text_tertiary, SIZE.icon_lg)
        )
