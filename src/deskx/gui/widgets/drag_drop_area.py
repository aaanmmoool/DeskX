"""Large drag-and-drop zone widget.

Provides visual feedback (dashed border changes, icon animation) when
the user drags a supported file over the area.  Emits
:pyqt:`file_dropped(str)` with the absolute path.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDragLeaveEvent, QDropEvent
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout

from deskx.core.config import SUPPORTED_EXTENSIONS


class DragDropArea(QFrame):
    """A large drop zone that accepts supported file types.

    Signals
    -------
    file_dropped(str)
        Emitted with the absolute file path when a valid file is dropped.
    """

    file_dropped = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("dropZone")
        self.setAcceptDrops(True)
        self.setMinimumHeight(220)
        self._setup_ui()

    # ── UI setup ────────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(12)
        layout.setContentsMargins(40, 40, 40, 40)

        # Icon
        self._icon_label = QLabel("📂")
        self._icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon_label.setStyleSheet("font-size: 40px; background: transparent; border: none;")
        layout.addWidget(self._icon_label)

        # Primary text
        self._title = QLabel("Drag & drop your file here")
        self._title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title.setProperty("role", "subheading")
        layout.addWidget(self._title)

        # Supported formats
        exts = "  •  ".join(
            ext.upper().lstrip(".") for ext in sorted(SUPPORTED_EXTENSIONS)
        )
        self._formats = QLabel(exts)
        self._formats.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._formats.setProperty("role", "caption")
        layout.addWidget(self._formats)

    # ── Drag-and-drop events ────────────────────────────────────────

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            url = event.mimeData().urls()[0]
            path = Path(url.toLocalFile())
            if path.suffix.lower() in SUPPORTED_EXTENSIONS:
                event.acceptProposedAction()
                self.setProperty("dragActive", True)
                self.style().unpolish(self)
                self.style().polish(self)
                self._title.setText("Drop to open")
                self._icon_label.setText("📥")
                return
        event.ignore()

    def dragLeaveEvent(self, event: QDragLeaveEvent) -> None:
        self._reset_visual()
        event.accept()

    def dropEvent(self, event: QDropEvent) -> None:
        self._reset_visual()
        if event.mimeData().hasUrls():
            url = event.mimeData().urls()[0]
            path = Path(url.toLocalFile())
            if path.suffix.lower() in SUPPORTED_EXTENSIONS:
                event.acceptProposedAction()
                self.file_dropped.emit(str(path))
                return
        event.ignore()

    # ── Internal ────────────────────────────────────────────────────

    def _reset_visual(self) -> None:
        self.setProperty("dragActive", False)
        self.style().unpolish(self)
        self.style().polish(self)
        self._title.setText("Drag & drop your file here")
        self._icon_label.setText("📂")
