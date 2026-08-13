"""Shared modal dialog chrome.

Every configuration dialog in DeskX derives from :class:`ModalDialog`
so they all share the same header, scrolling body, footer, keyboard
behaviour, and entrance animation.

    ┌────────────────────────────────────────────┐
    │ [icon]  Title                          [x] │  header
    │         Supporting sentence                │
    ├────────────────────────────────────────────┤
    │  … caller-provided content (scrolls) …     │  body
    ├────────────────────────────────────────────┤
    │ [left slot]              [Cancel] [Done]   │  footer
    └────────────────────────────────────────────┘

Dialogs are capped to ``SIZE.modal_max_height`` so they always fit on
a 1366x768 display; the body scrolls when content exceeds that.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from deskx.gui.theme import ColorPalette, SIZE, SPACE, palette
from deskx.gui.theme.icons import get_pixmap, icon_label
from deskx.gui.widgets.components import Button, IconButton, Themed, fade_in


class ModalDialog(QDialog, Themed):
    """Base class for all DeskX modals."""

    def __init__(
        self,
        title: str,
        subtitle: str = "",
        icon: str | None = None,
        width: int = 620,
        primary_text: str = "Done",
        cancel_text: str = "Cancel",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._icon_name = icon

        self.setWindowTitle(title)
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)
        self.setModal(True)
        self.setMinimumWidth(min(width, 560))
        self.resize(width, 0)
        self.setMaximumHeight(SIZE.modal_max_height)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header ──────────────────────────────────────────────────
        header = QFrame()
        header.setObjectName("modalHeader")
        head_row = QHBoxLayout(header)
        head_row.setContentsMargins(SPACE.xl, SPACE.lg, SPACE.md, SPACE.lg)
        head_row.setSpacing(SPACE.md)

        self._icon_lbl: QLabel | None = None
        if icon:
            self._icon_lbl = icon_label(icon, palette().primary, SIZE.icon_xl)
            head_row.addWidget(self._icon_lbl, 0, Qt.AlignmentFlag.AlignTop)

        text_col = QVBoxLayout()
        text_col.setContentsMargins(0, 0, 0, 0)
        text_col.setSpacing(2)

        self._title_lbl = QLabel(title)
        self._title_lbl.setObjectName("modalTitle")
        text_col.addWidget(self._title_lbl)

        self._subtitle_lbl = QLabel(subtitle)
        self._subtitle_lbl.setObjectName("modalSubtitle")
        self._subtitle_lbl.setWordWrap(True)
        self._subtitle_lbl.setVisible(bool(subtitle))
        text_col.addWidget(self._subtitle_lbl)

        head_row.addLayout(text_col, 1)

        self._close_btn = IconButton("close", "Close", 28)
        self._close_btn.clicked.connect(self.reject)
        head_row.addWidget(self._close_btn, 0, Qt.AlignmentFlag.AlignTop)

        root.addWidget(header)

        # ── Body ────────────────────────────────────────────────────
        body_frame = QFrame()
        body_frame.setObjectName("modalBody")
        body_wrap = QVBoxLayout(body_frame)
        body_wrap.setContentsMargins(0, 0, 0, 0)
        body_wrap.setSpacing(0)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        inner = QWidget()
        inner.setObjectName("pageRoot")
        self.content = QVBoxLayout(inner)
        self.content.setContentsMargins(SPACE.xl, SPACE.lg, SPACE.xl, SPACE.lg)
        self.content.setSpacing(SPACE.md)

        self._scroll.setWidget(inner)
        body_wrap.addWidget(self._scroll)
        root.addWidget(body_frame, 1)

        # ── Footer ──────────────────────────────────────────────────
        footer = QFrame()
        footer.setObjectName("modalFooter")
        self._footer_row = QHBoxLayout(footer)
        self._footer_row.setContentsMargins(SPACE.xl, SPACE.md, SPACE.xl, SPACE.md)
        self._footer_row.setSpacing(SPACE.sm)
        self._footer_row.addStretch()

        self.cancel_button = Button(cancel_text, role="ghost")
        self.cancel_button.clicked.connect(self.reject)
        self._footer_row.addWidget(self.cancel_button)

        self.primary_button = Button(primary_text, role="primary")
        self.primary_button.setDefault(True)
        self.primary_button.setAutoDefault(True)
        self.primary_button.clicked.connect(self._on_primary)
        self._footer_row.addWidget(self.primary_button)

        root.addWidget(footer)

        self._register_theme()

    # ── Public API ──────────────────────────────────────────────────

    def add_footer_widget(self, widget: QWidget) -> QWidget:
        """Insert a widget on the left-hand side of the footer."""
        self._footer_row.insertWidget(0, widget)
        return widget

    def set_subtitle(self, text: str) -> None:
        self._subtitle_lbl.setText(text)
        self._subtitle_lbl.setVisible(bool(text))

    def set_primary_enabled(self, enabled: bool) -> None:
        self.primary_button.setEnabled(enabled)

    def set_primary_text(self, text: str) -> None:
        self.primary_button.setText(text)

    # ── Hooks ───────────────────────────────────────────────────────

    def _on_primary(self) -> None:
        """Called when the primary CTA is pressed.  Override to validate."""
        self.accept()

    # ── Qt overrides ────────────────────────────────────────────────

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if not getattr(self, "_did_fade", False):
            self._did_fade = True
            self._size_to_content()
            fade_in(self)

    def _size_to_content(self) -> None:
        """Grow to fit the content, up to the 1366x768-safe ceiling."""
        wanted = self.layout().sizeHint().height()
        self.resize(self.width(), min(wanted, SIZE.modal_max_height))

    def apply_theme(self, p: ColorPalette) -> None:
        if self._icon_lbl is not None and self._icon_name:
            self._icon_lbl.setPixmap(
                get_pixmap(self._icon_name, p.primary, SIZE.icon_xl)
            )
