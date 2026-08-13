"""History screen.

Two lists, both built from data DeskX already keeps: the persisted
recent-files store, and the jobs completed during this session.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from deskx.core.utils import truncate_path
from deskx.gui.theme import SIZE, SPACE, palette
from deskx.gui.theme.icons import Icon, icon_label
from deskx.gui.widgets.components import (
    Badge,
    Button,
    Card,
    ClickableCard,
    EmptyState,
    SectionHeader,
    centered_page,
    clear_layout,
    label,
    scroll_container,
)
from deskx.history.recent_files import RecentFilesManager


class HistoryPage(QWidget):
    """Recently opened files and jobs completed this session.

    Signals
    -------
    file_selected(str)
        A recent file was chosen.
    """

    file_selected = Signal(str)

    def __init__(
        self,
        recent_manager: RecentFilesManager,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._recent = recent_manager
        self._jobs: list[dict] = []
        self._setup_ui()
        self.refresh()

    # ── Public API ──────────────────────────────────────────────────

    def add_job(self, report: dict) -> None:
        """Record a completed job (newest first)."""
        self._jobs.insert(0, report)
        self.refresh()

    def refresh(self) -> None:
        self._rebuild_files()
        self._rebuild_jobs()

    # ── Setup ───────────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        column = QWidget()
        column.setObjectName("pageRoot")
        col = QVBoxLayout(column)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(SPACE.lg)

        col.addWidget(label("History", "pageTitle"))
        col.addWidget(
            label(
                "Files you have opened and jobs you have run on this computer.",
                "subheading",
                wrap=True,
            )
        )

        # ── Recent files ───────────────────────────────────────────
        files_card = Card(padding=SPACE.xl, spacing=SPACE.md)
        header = SectionHeader("Recent files", Icon.FILES)
        clear_btn = Button("Clear list", icon=Icon.TRASH, role="ghost")
        clear_btn.setToolTip("Forget every remembered file path")
        clear_btn.clicked.connect(self._clear_recent)
        header.add_trailing(clear_btn)
        files_card.add(header)

        self._files_layout = QVBoxLayout()
        self._files_layout.setSpacing(SPACE.sm)
        files_card.add_layout(self._files_layout)

        self._files_empty = EmptyState(
            Icon.FILES,
            "Nothing opened yet",
            "Files you work on will be listed here.",
        )
        files_card.add(self._files_empty)
        col.addWidget(files_card)

        # ── Jobs ───────────────────────────────────────────────────
        jobs_card = Card(padding=SPACE.xl, spacing=SPACE.md)
        jobs_card.add(
            SectionHeader(
                "Jobs in this session",
                Icon.CLOCK,
                "Cleared when DeskX closes.",
            )
        )

        self._jobs_layout = QVBoxLayout()
        self._jobs_layout.setSpacing(SPACE.sm)
        jobs_card.add_layout(self._jobs_layout)

        self._jobs_empty = EmptyState(
            Icon.PROCESS,
            "No jobs yet",
            "Process a file and the run will be summarized here.",
        )
        jobs_card.add(self._jobs_empty)
        col.addWidget(jobs_card)

        col.addStretch()

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(scroll_container(centered_page(column, max_width=960)))

    # ── Rendering ───────────────────────────────────────────────────

    def _rebuild_files(self) -> None:
        clear_layout(self._files_layout)
        entries = self._recent.entries
        self._files_empty.setVisible(not entries)

        for entry in entries:
            self._files_layout.addWidget(
                self._make_file_row(Path(entry.path), entry.last_opened)
            )

    def _make_file_row(self, path: Path, last_opened: str) -> QWidget:
        exists = path.is_file()
        card = ClickableCard(padding=SPACE.md, spacing=0, variant="cardFlat")

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(SPACE.md)

        tone = palette().primary if exists else palette().text_tertiary
        row.addWidget(icon_label(Icon.FILE, tone, SIZE.icon_lg))

        col = QVBoxLayout()
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(0)
        col.addWidget(label(path.name, "body"))
        col.addWidget(label(truncate_path(path.parent, 56), "caption"))
        row.addLayout(col, 1)

        row.addWidget(label(_relative_time(last_opened), "caption"))
        if not exists:
            row.addWidget(Badge("Missing", "error"))

        card.add_layout(row)
        card.setToolTip(str(path))

        if exists:
            card.clicked.connect(lambda p=str(path): self.file_selected.emit(p))
        else:
            card.setCursor(Qt.CursorShape.ArrowCursor)

        return card

    def _rebuild_jobs(self) -> None:
        clear_layout(self._jobs_layout)
        self._jobs_empty.setVisible(not self._jobs)

        for report in self._jobs:
            self._jobs_layout.addWidget(self._make_job_row(report))

    def _make_job_row(self, report: dict) -> QWidget:
        card = Card(padding=SPACE.md, spacing=0, variant="cardFlat")

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(SPACE.md)

        status = report.get("status", "success")
        tone = {"success": "success", "cancelled": "warning"}.get(status, "error")
        icon = {
            "success": Icon.SUCCESS,
            "cancelled": Icon.WARNING,
        }.get(status, Icon.ERROR)
        row.addWidget(
            icon_label(icon, getattr(palette(), tone), SIZE.icon_lg)
        )

        col = QVBoxLayout()
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(0)
        output = Path(report.get("output_path", "")).name or "—"
        col.addWidget(label(output, "body"))

        details = []
        if report.get("row_count") is not None:
            details.append(f"{int(report['row_count']):,} rows")
        if report.get("column_count") is not None:
            details.append(f"{int(report['column_count'])} columns")
        if report.get("duration_seconds") is not None:
            details.append(f"{float(report['duration_seconds']):.2f}s")
        col.addWidget(label("   ·   ".join(details), "caption"))
        row.addLayout(col, 1)

        row.addWidget(Badge(status.title(), tone))
        card.add_layout(row)
        return card

    def _clear_recent(self) -> None:
        self._recent.clear()
        self.refresh()


def _relative_time(iso_timestamp: str) -> str:
    """Render an ISO-8601 timestamp as a short relative description."""
    try:
        moment = datetime.fromisoformat(iso_timestamp)
    except (TypeError, ValueError):
        return ""

    now = datetime.now(moment.tzinfo)
    delta = now - moment
    seconds = delta.total_seconds()

    if seconds < 60:
        return "just now"
    if seconds < 3600:
        return f"{int(seconds // 60)} min ago"
    if seconds < 86400:
        return f"{int(seconds // 3600)} h ago"
    if seconds < 604800:
        return f"{int(seconds // 86400)} d ago"
    return moment.strftime("%d %b %Y")
