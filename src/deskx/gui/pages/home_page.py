"""Home dashboard — the first thing the user sees.

Presents the greeting, the two ways into the workflow, and a summary
of activity that already exists in the app (recent files from the MRU
store, the last completed job's report).  No metric on this screen is
invented: if the data isn't available, the card says so.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
)

from deskx.core.config import SUPPORTED_EXTENSIONS
from deskx.core.utils import truncate_path
from deskx.gui.theme import ColorPalette, SIZE, SPACE, palette
from deskx.gui.theme.icons import Icon, get_pixmap, icon_label
from deskx.gui.widgets.components import (
    Button,
    Card,
    ClickableCard,
    EmptyState,
    SectionHeader,
    StatCard,
    Themed,
    centered_page,
    clear_layout,
    label,
    scroll_container,
)
from deskx.history.recent_files import RecentFilesManager
from deskx.processing.transform_catalog import TRANSFORM_CATALOG


class HomePage(QWidget, Themed):
    """Dashboard with quick actions, activity, and privacy reassurance.

    Signals
    -------
    open_file_requested()
        The user wants to pick a file.
    open_sample_requested()
        The user wants to load the bundled sample dataset.
    file_selected(str)
        A recent file was chosen from the dashboard.
    view_history_requested()
        Navigate to the History screen.
    """

    open_file_requested = Signal()
    open_sample_requested = Signal()
    file_selected = Signal(str)
    view_history_requested = Signal()

    def __init__(
        self,
        recent_manager: RecentFilesManager,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._recent = recent_manager
        self._recent_cards: list[QWidget] = []
        self._setup_ui()
        self.refresh()
        self._register_theme()

    # ── Public API ──────────────────────────────────────────────────

    def refresh(self, last_report: dict | None = None) -> None:
        """Rebuild activity cards from live data."""
        self._rebuild_recent()
        self._update_stats(last_report)

    # ── Construction ────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        column = QWidget()
        column.setObjectName("pageRoot")
        col = QVBoxLayout(column)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(SPACE.xl)

        col.addWidget(self._build_greeting())
        col.addWidget(self._build_actions())
        col.addLayout(self._build_stats())

        lower = QHBoxLayout()
        lower.setSpacing(SPACE.lg)
        lower.addWidget(self._build_recent_card(), 3)
        lower.addWidget(self._build_privacy_card(), 2)
        col.addLayout(lower)

        col.addStretch()

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(scroll_container(centered_page(column)))

    def _build_greeting(self) -> QWidget:
        block = QWidget()
        col = QVBoxLayout(block)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(SPACE.xs)

        col.addWidget(label(_today_label(), "caption"))

        self._greeting = label("Welcome to DeskX", "display")
        col.addWidget(self._greeting)

        col.addWidget(label("Prepare your data safely.", "displayAccent"))
        col.addSpacing(SPACE.xs)
        col.addWidget(
            label(
                "DeskX cleans and anonymizes spreadsheets on your own computer, "
                "then writes the result to a brand-new file so the original is "
                "never touched.",
                "subheading",
                wrap=True,
            )
        )
        return block

    def _build_actions(self) -> QWidget:
        card = Card(padding=SPACE.xl, spacing=SPACE.md, elevated=True)

        card.add(
            SectionHeader(
                "Start a job",
                Icon.SPARKLE,
                "Pick a dataset and DeskX walks you through preview, cleaning, and saving.",
            )
        )

        row = QHBoxLayout()
        row.setSpacing(SPACE.sm)

        primary = Button(
            "Process a file",
            icon=Icon.UPLOAD,
            role="primary",
            height=SIZE.control_height_lg,
        )
        primary.setMinimumWidth(180)
        primary.clicked.connect(self.open_file_requested.emit)
        row.addWidget(primary)

        sample = Button(
            "Open sample data",
            icon=Icon.TABLE,
            role="ghost",
            height=SIZE.control_height_lg,
        )
        sample.setToolTip("Load a small demo dataset to explore DeskX safely")
        sample.clicked.connect(self.open_sample_requested.emit)
        row.addWidget(sample)

        row.addStretch()
        card.add_layout(row)

        formats = "  ·  ".join(
            ext.upper().lstrip(".") for ext in sorted(SUPPORTED_EXTENSIONS)
        )
        card.add(label(f"Supported formats    {formats}", "caption"))
        return card

    def _build_stats(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(SPACE.lg)

        self._stat_files = StatCard(
            "Files in your history", "0", Icon.FILES, "primary"
        )
        self._stat_rows = StatCard(
            "Rows in your last job", "—", Icon.TABLE, "secondary"
        )
        self._stat_transforms = StatCard(
            "Available transformations",
            str(len(TRANSFORM_CATALOG)),
            Icon.TRANSFORM,
            "primary",
        )

        row.addWidget(self._stat_files)
        row.addWidget(self._stat_rows)
        row.addWidget(self._stat_transforms)
        return row

    def _build_recent_card(self) -> QWidget:
        self._recent_card = Card(padding=SPACE.xl, spacing=SPACE.md)

        header = SectionHeader("Recent files", Icon.HISTORY)
        view_all = Button("View all", role="link")
        view_all.clicked.connect(self.view_history_requested.emit)
        header.add_trailing(view_all)
        self._recent_card.add(header)

        self._recent_list = QVBoxLayout()
        self._recent_list.setSpacing(SPACE.sm)
        self._recent_card.add_layout(self._recent_list)

        self._recent_empty = EmptyState(
            Icon.FILES,
            "No files yet",
            "Datasets you open will appear here for quick access.",
        )
        self._recent_card.add(self._recent_empty)
        self._recent_card.body.addStretch()
        return self._recent_card

    def _build_privacy_card(self) -> QWidget:
        card = Card(padding=SPACE.xl, spacing=SPACE.md)
        card.add(SectionHeader("How DeskX keeps you safe", Icon.PRIVACY))

        self._promise_rows: list[tuple[QWidget, str]] = []
        promises = (
            (Icon.LOCK, "Everything runs offline. No network requests, ever."),
            (Icon.SHIELD, "The source file is opened read-only and never rewritten."),
            (Icon.SUCCESS, "Output is written to a temporary file, then promoted."),
            (Icon.HASH, "Source and output are SHA-256 hashed for the audit report."),
        )
        for icon_name, text in promises:
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(SPACE.sm)
            glyph = icon_label(icon_name, palette().success, SIZE.icon_md)
            row_layout.addWidget(glyph, 0, Qt.AlignmentFlag.AlignTop)
            row_layout.addWidget(label(text, "body", wrap=True), 1)
            card.add(row)
            self._promise_rows.append((glyph, icon_name))

        card.body.addStretch()
        return card

    # ── Data ────────────────────────────────────────────────────────

    def _rebuild_recent(self) -> None:
        clear_layout(self._recent_list)

        entries = self._recent.entries[:4]
        self._recent_empty.setVisible(not entries)

        for entry in entries:
            self._recent_list.addWidget(self._make_recent_row(entry.path))

    def _make_recent_row(self, path_str: str) -> QWidget:
        path = Path(path_str)
        exists = path.is_file()

        card = ClickableCard(padding=SPACE.md, spacing=0, variant="cardFlat")
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(SPACE.md)

        tone = palette().primary if exists else palette().text_tertiary
        row.addWidget(icon_label(_format_icon(path.suffix), tone, SIZE.icon_lg))

        text_col = QVBoxLayout()
        text_col.setContentsMargins(0, 0, 0, 0)
        text_col.setSpacing(0)
        name = label(path.name, "cardTitle" if exists else "body")
        text_col.addWidget(name)
        detail = (
            truncate_path(path.parent, 46) if exists else "File is no longer available"
        )
        text_col.addWidget(label(detail, "caption"))
        row.addLayout(text_col, 1)

        card.add_layout(row)
        card.setToolTip(str(path))

        if exists:
            card.clicked.connect(lambda p=str(path): self.file_selected.emit(p))
        else:
            card.setCursor(Qt.CursorShape.ArrowCursor)
            card.setProperty("interactive", "false")

        return card

    def _update_stats(self, last_report: dict | None) -> None:
        entries = self._recent.entries
        self._stat_files.set_value(
            str(len(entries)),
            "Opened on this computer" if entries else "Nothing opened yet",
        )

        if last_report and last_report.get("row_count") is not None:
            rows = int(last_report["row_count"])
            columns = last_report.get("column_count")
            hint = f"{columns} columns written" if columns else ""
            self._stat_rows.set_value(f"{rows:,}", hint)
        else:
            self._stat_rows.set_value("—", "Run a job to see this")

        self._stat_transforms.set_value(
            str(len(TRANSFORM_CATALOG)), "Cleaning, privacy, and formatting"
        )

    def apply_theme(self, p: ColorPalette) -> None:
        for glyph, icon_name in getattr(self, "_promise_rows", []):
            glyph.setPixmap(get_pixmap(icon_name, p.success, SIZE.icon_md))


def _today_label() -> str:
    """Return a friendly date line, e.g. ``Mon, 11 August``."""
    return datetime.now().strftime("%a, %d %B").replace(" 0", " ")


def _format_icon(suffix: str) -> str:
    return {
        ".xlsx": Icon.SPREADSHEET,
        ".csv": Icon.TABLE,
        ".json": Icon.DATABASE,
        ".txt": Icon.FILE,
    }.get(suffix.lower(), Icon.FILE)
