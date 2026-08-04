"""Vertical navigation rail.

Minimal icon + label buttons arranged vertically, highlighting the
current step.  Inspired by Linear's sidebar navigation.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class NavButton(QPushButton):
    """A single navigation item with icon and label."""

    def __init__(
        self,
        icon_text: str,
        label: str,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setProperty("role", "ghost")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setCheckable(True)
        self.setMinimumHeight(44)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(12)

        icon = QLabel(icon_text)
        icon.setStyleSheet("font-size: 16px; background: transparent; border: none;")
        icon.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        layout.addWidget(icon)

        text = QLabel(label)
        text.setStyleSheet("background: transparent; border: none;")
        text.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        layout.addWidget(text)

        layout.addStretch()


class NavBar(QWidget):
    """Vertical navigation bar with step buttons.

    Signals
    -------
    page_changed(int)
        Emitted when the user clicks a different nav item, with the
        zero-based page index.
    """

    page_changed = Signal(int)

    # ── Nav items (icon, label) ─────────────────────────────────────
    _ITEMS = [
        ("📤", "Upload"),
        ("👁", "Preview"),
        ("📋", "Results"),
    ]

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("navBar")
        self.setFixedWidth(200)
        self._buttons: list[NavButton] = []
        self._setup_ui()
        # Select the first item
        if self._buttons:
            self._buttons[0].setChecked(True)

    # ── Public API ──────────────────────────────────────────────────

    def set_current_index(self, index: int) -> None:
        """Programmatically select a nav item."""
        if 0 <= index < len(self._buttons):
            for btn in self._buttons:
                btn.setChecked(False)
            self._buttons[index].setChecked(True)

    # ── Setup ───────────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 20, 12, 20)
        layout.setSpacing(4)

        # App title
        title = QLabel("DeskX")
        title.setProperty("role", "heading")
        title.setStyleSheet("font-size: 20px;")
        title.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(title)

        layout.addSpacing(24)

        # Nav buttons
        for idx, (icon, label) in enumerate(self._ITEMS):
            btn = NavButton(icon, label)
            btn.clicked.connect(lambda checked, i=idx: self._on_click(i))
            self._buttons.append(btn)
            layout.addWidget(btn)

        layout.addStretch()

        # Theme toggle
        self._theme_btn = QPushButton("🌙  Dark Mode")
        self._theme_btn.setProperty("role", "ghost")
        self._theme_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._theme_btn.setMinimumHeight(40)
        layout.addWidget(self._theme_btn)

        # Version label
        from deskx.core.config import APP_VERSION

        version = QLabel(f"v{APP_VERSION}")
        version.setProperty("role", "caption")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version)

    @property
    def theme_button(self) -> QPushButton:
        """Access the theme toggle button."""
        return self._theme_btn

    def update_theme_button(self, is_dark: bool) -> None:
        """Update the theme button text to reflect current mode."""
        self._theme_btn.setText(
            "☀️  Light Mode" if is_dark else "🌙  Dark Mode"
        )

    # ── Slots ───────────────────────────────────────────────────────

    def _on_click(self, index: int) -> None:
        for i, btn in enumerate(self._buttons):
            btn.setChecked(i == index)
        self.page_changed.emit(index)
