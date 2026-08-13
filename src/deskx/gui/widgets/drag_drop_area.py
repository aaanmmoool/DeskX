"""Large drag-and-drop zone widget.

Gives clear visual feedback while a supported file is dragged over it
and emits :pyqt:`file_dropped(str)` with the absolute path on drop.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDragLeaveEvent, QDropEvent
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout

from deskx.core.config import SUPPORTED_EXTENSIONS
from deskx.gui.theme import ColorPalette, SPACE, palette
from deskx.gui.theme.icons import Icon, get_pixmap, icon_label
from deskx.gui.theme.stylesheet import repolish
from deskx.gui.widgets.components import Badge, Themed, label

_IDLE_TITLE = "Drop your dataset here"
_IDLE_SUBTITLE = "or browse from your computer"
_ACTIVE_TITLE = "Release to open"
_ACTIVE_SUBTITLE = "DeskX will read a preview — your file stays as it is"


class DragDropArea(QFrame, Themed):
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
        self.setMinimumHeight(260)
        self._setup_ui()
        self._register_theme()

    # ── UI setup ────────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(SPACE.sm)
        layout.setContentsMargins(SPACE.huge, SPACE.xxxl, SPACE.huge, SPACE.xxxl)

        self._icon_label = icon_label(Icon.UPLOAD, palette().primary, 40, 1.6)
        layout.addWidget(self._icon_label, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addSpacing(SPACE.sm)

        self._title = label(_IDLE_TITLE, "sectionTitle")
        self._title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._title)

        self._subtitle = label(_IDLE_SUBTITLE, "body")
        self._subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._subtitle)

        layout.addSpacing(SPACE.md)

        formats = QHBoxLayout()
        formats.setSpacing(SPACE.sm)
        formats.setAlignment(Qt.AlignmentFlag.AlignCenter)
        for ext in sorted(SUPPORTED_EXTENSIONS):
            formats.addWidget(Badge(ext.upper().lstrip("."), "neutral"))
        layout.addLayout(formats)

    # ── Drag-and-drop events ────────────────────────────────────────

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            url = event.mimeData().urls()[0]
            path = Path(url.toLocalFile())
            if path.suffix.lower() in SUPPORTED_EXTENSIONS:
                event.acceptProposedAction()
                self._set_active(True)
                return
        event.ignore()

    def dragLeaveEvent(self, event: QDragLeaveEvent) -> None:
        self._set_active(False)
        event.accept()

    def dropEvent(self, event: QDropEvent) -> None:
        self._set_active(False)
        if event.mimeData().hasUrls():
            url = event.mimeData().urls()[0]
            path = Path(url.toLocalFile())
            if path.suffix.lower() in SUPPORTED_EXTENSIONS:
                event.acceptProposedAction()
                self.file_dropped.emit(str(path))
                return
        event.ignore()

    # ── Internal ────────────────────────────────────────────────────

    def _set_active(self, active: bool) -> None:
        self.setProperty("dragActive", active)
        repolish(self)
        self._title.setText(_ACTIVE_TITLE if active else _IDLE_TITLE)
        self._subtitle.setText(_ACTIVE_SUBTITLE if active else _IDLE_SUBTITLE)
        self._icon_label.setPixmap(
            get_pixmap(
                Icon.DOWNLOAD if active else Icon.UPLOAD,
                palette().primary,
                40,
                1.6,
            )
        )

    def apply_theme(self, p: ColorPalette) -> None:
        active = bool(self.property("dragActive"))
        self._icon_label.setPixmap(
            get_pixmap(Icon.DOWNLOAD if active else Icon.UPLOAD, p.primary, 40, 1.6)
        )
