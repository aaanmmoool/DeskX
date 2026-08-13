"""Primary navigation rail.

A persistent left-hand sidebar holding the DeskX wordmark, the main
destinations, and a footer with Help and Privacy.  Navigation is
purely presentational — every destination maps to a screen that
already existed in some form.
"""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QEvent, QSize, Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from deskx.gui.theme import ColorPalette, SIZE, SPACE, palette
from deskx.gui.theme.icons import Icon, get_icon, get_pixmap, icon_label
from deskx.gui.theme.stylesheet import repolish
from deskx.gui.widgets.components import Themed, label


@dataclass(frozen=True)
class NavItem:
    """One destination in the rail."""

    key: str
    text: str
    icon: str
    tooltip: str = ""


class _NavButton(QPushButton, Themed):
    """A single navigation entry that tints its icon with its state."""

    def __init__(self, item: NavItem, parent: QWidget | None = None) -> None:
        super().__init__(item.text, parent)
        self.item = item
        self.setProperty("nav", "true")
        self.setProperty("active", "false")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(item.tooltip or item.text)
        self.setAccessibleName(item.text)
        self.setIconSize(QSize(SIZE.icon_lg, SIZE.icon_lg))
        self._register_theme()

    def set_active(self, active: bool) -> None:
        self.setProperty("active", "true" if active else "false")
        repolish(self)
        self.apply_theme(palette())

    def apply_theme(self, p: ColorPalette) -> None:
        active = self.property("active") == "true"
        if not self.isEnabled():
            color = p.text_tertiary
        else:
            color = p.primary if active else p.text_secondary
        self.setIcon(get_icon(self.item.icon, color, SIZE.icon_lg))

    def changeEvent(self, event) -> None:
        super().changeEvent(event)
        # Keep the icon in step with the enabled state.
        if event.type() == QEvent.Type.EnabledChange:
            self.apply_theme(palette())


class SidebarNav(QWidget, Themed):
    """The application's left navigation rail.

    Signals
    -------
    navigated(str)
        Emitted with the destination key when the user picks an item.
    """

    navigated = Signal(str)

    PRIMARY_ITEMS = (
        NavItem("home", "Home", Icon.HOME, "Dashboard and quick actions"),
        NavItem("files", "Files", Icon.FILES, "Open a dataset"),
        NavItem("transform", "Transform", Icon.TRANSFORM, "Preview, clean, and protect data"),
        NavItem("history", "History", Icon.HISTORY, "Recent files and jobs"),
        NavItem("reports", "Reports", Icon.REPORTS, "Audit report for the last job"),
        NavItem("settings", "Settings", Icon.SETTINGS, "Appearance and save location"),
    )

    FOOTER_ITEMS = (
        NavItem("help", "Help", Icon.HELP, "Open the user guide (F1)"),
        NavItem("privacy", "Privacy", Icon.PRIVACY, "How DeskX protects your data"),
    )

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(SIZE.sidebar_width)

        self._buttons: dict[str, _NavButton] = {}
        self._current = "home"

        root = QVBoxLayout(self)
        root.setContentsMargins(SPACE.md, SPACE.lg, SPACE.md, SPACE.md)
        root.setSpacing(SPACE.xs)

        root.addWidget(self._build_brand())
        root.addSpacing(SPACE.lg)

        section = label("WORKSPACE", "eyebrow")
        section.setObjectName("navSectionLabel")
        root.addWidget(section)
        root.addSpacing(SPACE.xs)

        for item in self.PRIMARY_ITEMS:
            root.addWidget(self._make_button(item))

        root.addStretch()

        root.addWidget(self._build_privacy_note())
        root.addSpacing(SPACE.sm)

        rule = QFrame()
        rule.setProperty("role", "separator")
        root.addWidget(rule)
        root.addSpacing(SPACE.xs)

        for item in self.FOOTER_ITEMS:
            root.addWidget(self._make_button(item))

        self.set_current("home")
        self._register_theme()

    # ── Construction ────────────────────────────────────────────────

    def _build_brand(self) -> QWidget:
        brand = QWidget()
        row = QHBoxLayout(brand)
        row.setContentsMargins(SPACE.sm, 0, SPACE.sm, 0)
        row.setSpacing(SPACE.sm + 2)

        self._brand_mark = icon_label(Icon.SHIELD, palette().primary, 26)
        row.addWidget(self._brand_mark)

        text_col = QVBoxLayout()
        text_col.setContentsMargins(0, 0, 0, 0)
        text_col.setSpacing(0)

        name = QLabel("DeskX")
        name.setObjectName("brandName")
        text_col.addWidget(name)

        tag = QLabel("Data sanitizer")
        tag.setObjectName("brandTag")
        text_col.addWidget(tag)

        row.addLayout(text_col)
        row.addStretch()
        return brand

    def _build_privacy_note(self) -> QWidget:
        card = QFrame()
        card.setProperty("role", "accentCard")
        col = QVBoxLayout(card)
        col.setContentsMargins(SPACE.md, SPACE.md, SPACE.md, SPACE.md)
        col.setSpacing(SPACE.xs + 2)

        head = QHBoxLayout()
        head.setContentsMargins(0, 0, 0, 0)
        head.setSpacing(SPACE.xs + 2)
        self._note_icon = icon_label(Icon.LOCK, palette().primary, SIZE.icon_md)
        head.addWidget(self._note_icon)
        title = label("Fully offline", "caption", tone="primary")
        head.addWidget(title)
        head.addStretch()
        col.addLayout(head)

        body = label(
            "Your files are processed on this device. Nothing is uploaded.",
            "caption",
            wrap=True,
        )
        col.addWidget(body)
        return card

    def _make_button(self, item: NavItem) -> _NavButton:
        button = _NavButton(item)
        button.clicked.connect(lambda _=False, key=item.key: self.navigated.emit(key))
        self._buttons[item.key] = button
        return button

    # ── Public API ──────────────────────────────────────────────────

    def set_current(self, key: str) -> None:
        """Highlight the destination identified by *key*."""
        self._current = key
        for item_key, button in self._buttons.items():
            button.set_active(item_key == key)

    def current(self) -> str:
        return self._current

    def set_enabled_item(self, key: str, enabled: bool) -> None:
        """Enable or disable a single destination (e.g. Transform)."""
        button = self._buttons.get(key)
        if button is not None:
            button.setEnabled(enabled)

    def apply_theme(self, p: ColorPalette) -> None:
        self._brand_mark.setPixmap(get_pixmap(Icon.SHIELD, p.primary, 26))
        self._note_icon.setPixmap(get_pixmap(Icon.LOCK, p.primary, SIZE.icon_md))
