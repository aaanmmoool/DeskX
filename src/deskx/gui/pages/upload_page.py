"""Upload screen — first thing the user sees.

A clean, centered layout with:
* Big drag-and-drop zone
* Browse button
* Recent files list

Output folder is automatically the same as the source file,
so no folder picker is needed here.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from deskx.core.config import FILE_FILTER_STRING
from deskx.gui.widgets.drag_drop_area import DragDropArea
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

    # ── Setup ───────────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        # Center everything in a max-width container
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        container = QWidget()
        container.setMaximumWidth(680)
        container.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )

        root = QVBoxLayout(container)
        root.setContentsMargins(40, 60, 40, 40)
        root.setSpacing(0)

        # ── Heading ─────────────────────────────────────────────────
        heading = QLabel("Upload a Dataset")
        heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        heading.setProperty("role", "heading")
        heading.setStyleSheet("font-size: 26px;")
        root.addWidget(heading)

        root.addSpacing(6)

        subtitle = QLabel(
            "Drop a file below to preview, transform, and sanitize your data."
        )
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setProperty("role", "subheading")
        subtitle.setWordWrap(True)
        root.addWidget(subtitle)

        root.addSpacing(32)

        # ── Drop zone ──────────────────────────────────────────────
        self._drop_area = DragDropArea()
        self._drop_area.file_dropped.connect(self._on_file_chosen)
        root.addWidget(self._drop_area)

        root.addSpacing(16)

        # ── Browse & Sample buttons (centered) ──────────────────────
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)
        btn_row.addStretch()

        self._browse_btn = QPushButton("📁  Browse Files")
        self._browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._browse_btn.setMinimumHeight(44)
        self._browse_btn.setMinimumWidth(160)
        self._browse_btn.setProperty("role", "primary")
        self._browse_btn.clicked.connect(self._on_browse)
        btn_row.addWidget(self._browse_btn)

        self._sample_btn = QPushButton("🎁  Try Sample Data")
        self._sample_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._sample_btn.setMinimumHeight(44)
        self._sample_btn.setMinimumWidth(160)
        self._sample_btn.setProperty("role", "ghost")
        self._sample_btn.clicked.connect(self._on_load_sample)
        btn_row.addWidget(self._sample_btn)

        btn_row.addStretch()
        root.addLayout(btn_row)

        root.addSpacing(32)

        # ── Recent files ───────────────────────────────────────────
        self._recent_section = QWidget()
        recent_layout = QVBoxLayout(self._recent_section)
        recent_layout.setContentsMargins(0, 0, 0, 0)
        recent_layout.setSpacing(8)

        recent_header = QLabel("Recently Opened")
        recent_header.setProperty("role", "caption")
        recent_header.setStyleSheet("font-weight: 600; text-transform: uppercase; letter-spacing: 1px;")
        recent_layout.addWidget(recent_header)

        self._recent_list = QListWidget()
        self._recent_list.setMaximumHeight(180)
        self._recent_list.itemDoubleClicked.connect(
            self._on_recent_clicked
        )
        recent_layout.addWidget(self._recent_list)

        root.addWidget(self._recent_section)
        root.addStretch()

        outer.addWidget(container)

    # ── Slots ───────────────────────────────────────────────────────

    def _on_browse(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Select File", "", FILE_FILTER_STRING
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
            p = Path(entry.path)
            display = f"{p.name}   —   {p.parent}"
            item = QListWidgetItem(display)
            item.setData(Qt.ItemDataRole.UserRole, entry.path)
            if not p.is_file():
                item.setForeground(
                    self.palette().color(
                        self.palette().currentColorGroup(),
                        self.palette().ColorRole.PlaceholderText,
                    )
                )
            self._recent_list.addItem(item)
