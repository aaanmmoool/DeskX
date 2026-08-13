"""Upload screen — step one of the workflow.

A single, uncrowded decision: which dataset do you want to work on?
The drop zone dominates, browse and sample sit directly beneath it,
and recently opened files are one click away.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from deskx.core.config import FILE_FILTER_STRING
from deskx.core.utils import truncate_path
from deskx.gui.theme import SIZE, SPACE
from deskx.gui.theme.icons import Icon
from deskx.gui.widgets.components import (
    Button,
    Card,
    SectionHeader,
    StepIndicator,
    centered_page,
    label,
    scroll_container,
)
from deskx.gui.widgets.drag_drop_area import DragDropArea
from deskx.gui.workflow import STEP_UPLOAD, WORKFLOW_STEPS
from deskx.history.recent_files import RecentFilesManager
from deskx.samples import get_sample_employee_dataset_path


class UploadPage(QWidget):
    """File selection screen.

    Signals
    -------
    file_selected(str)
        Emitted with the absolute path when a file is chosen.
    """

    file_selected = Signal(str)

    def __init__(
        self,
        recent_manager: RecentFilesManager,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._recent = recent_manager
        self._setup_ui()
        self._refresh_recent_list()

    # ── Public API ──────────────────────────────────────────────────

    def refresh(self) -> None:
        """Re-read the recent-files store."""
        self._refresh_recent_list()

    # ── Setup ───────────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        column = QWidget()
        column.setObjectName("pageRoot")
        col = QVBoxLayout(column)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(SPACE.lg)

        steps = StepIndicator(WORKFLOW_STEPS)
        steps.set_current(STEP_UPLOAD)
        col.addWidget(steps)

        heading = QVBoxLayout()
        heading.setSpacing(SPACE.xs)
        heading.addWidget(label("Choose a dataset", "pageTitle"))
        heading.addWidget(
            label(
                "Drop a file below to preview it, apply cleaning and privacy "
                "rules, then save a sanitized copy.",
                "subheading",
                wrap=True,
            )
        )
        col.addLayout(heading)

        card = Card(padding=SPACE.xl, spacing=SPACE.lg, elevated=True)

        self._drop_area = DragDropArea()
        self._drop_area.file_dropped.connect(self._on_file_chosen)
        card.add(self._drop_area)

        buttons = QHBoxLayout()
        buttons.setSpacing(SPACE.sm)
        buttons.addStretch()

        self._browse_btn = Button(
            "Browse files",
            icon=Icon.FOLDER_OPEN,
            role="primary",
            height=SIZE.control_height_lg,
        )
        self._browse_btn.setMinimumWidth(170)
        self._browse_btn.clicked.connect(self._on_browse)
        buttons.addWidget(self._browse_btn)

        self._sample_btn = Button(
            "Try sample data",
            icon=Icon.TABLE,
            role="ghost",
            height=SIZE.control_height_lg,
        )
        self._sample_btn.setToolTip("Load a small demo dataset to explore DeskX")
        self._sample_btn.clicked.connect(self._on_load_sample)
        buttons.addWidget(self._sample_btn)

        buttons.addStretch()
        card.add_layout(buttons)
        col.addWidget(card)

        # ── Recent files ───────────────────────────────────────────
        self._recent_section = Card(padding=SPACE.xl, spacing=SPACE.md)
        self._recent_section.add(
            SectionHeader(
                "Recently opened",
                Icon.HISTORY,
                "Double-click a file to open it again.",
            )
        )

        self._recent_list = QListWidget()
        self._recent_list.setMaximumHeight(190)
        self._recent_list.setSpacing(2)
        self._recent_list.itemDoubleClicked.connect(self._on_recent_clicked)
        self._recent_list.itemActivated.connect(self._on_recent_clicked)
        self._recent_section.add(self._recent_list)
        col.addWidget(self._recent_section)

        col.addStretch()

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(scroll_container(centered_page(column, max_width=880)))

    # ── Slots ───────────────────────────────────────────────────────

    def _on_browse(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Select a dataset", "", FILE_FILTER_STRING
        )
        if path:
            self._on_file_chosen(path)

    def _on_file_chosen(self, path: str) -> None:
        self._recent.add(Path(path))
        self._refresh_recent_list()
        self.file_selected.emit(path)

    def _on_load_sample(self) -> None:
        sample_path = get_sample_employee_dataset_path()
        if sample_path.exists():
            self._on_file_chosen(str(sample_path.resolve()))

    def _on_recent_clicked(self, item: QListWidgetItem) -> None:
        path = item.data(Qt.ItemDataRole.UserRole)
        if path and Path(path).is_file():
            self._on_file_chosen(path)

    # ── Recent files ────────────────────────────────────────────────

    def _refresh_recent_list(self) -> None:
        self._recent_list.clear()
        entries = self._recent.entries
        self._recent_section.setVisible(bool(entries))

        for entry in entries:
            path = Path(entry.path)
            exists = path.is_file()
            item = QListWidgetItem(
                f"{path.name}      {truncate_path(path.parent, 48)}"
            )
            item.setData(Qt.ItemDataRole.UserRole, entry.path)
            item.setToolTip(
                str(path) if exists else f"{path}\n\nThis file is no longer available."
            )
            if not exists:
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
            self._recent_list.addItem(item)
