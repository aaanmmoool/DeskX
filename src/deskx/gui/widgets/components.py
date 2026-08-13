"""Shared building blocks for the DeskX interface.

Every screen is assembled from these primitives so spacing, radii,
icon sizing, and hover behaviour stay identical everywhere.  Widgets
here never hard-code a colour: they read tokens from
:mod:`deskx.gui.theme` and re-tint themselves when the theme changes.
"""

from __future__ import annotations

from typing import Callable, Iterable

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from deskx.gui.theme import ColorPalette, RADIUS, SIZE, SPACE, palette, subscribe, unsubscribe
from deskx.gui.theme.icons import Icon, get_icon, get_pixmap, icon_label
from deskx.gui.theme.stylesheet import repolish


# ── Theme plumbing ──────────────────────────────────────────────────


class Themed:
    """Mixin that calls ``apply_theme`` whenever the palette changes.

    Subclasses implement ``apply_theme(palette)`` to re-tint anything
    the stylesheet cannot reach (rendered icon pixmaps, drop shadows).
    """

    def _register_theme(self) -> None:
        def _on_change(p: ColorPalette) -> None:
            try:
                self.apply_theme(p)  # type: ignore[attr-defined]
            except RuntimeError:
                # The underlying C++ object is gone — stop listening.
                unsubscribe(_on_change)

        self._theme_listener = _on_change
        subscribe(_on_change)
        self.apply_theme(palette())  # type: ignore[attr-defined]

    def apply_theme(self, p: ColorPalette) -> None:  # pragma: no cover - default
        """Re-tint theme-dependent visuals.  Overridden by subclasses."""


def apply_shadow(
    widget: QWidget,
    blur: int = 24,
    y_offset: int = 4,
    p: ColorPalette | None = None,
) -> QGraphicsDropShadowEffect:
    """Attach a soft elevation shadow to *widget*."""
    pal = p or palette()
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(blur)
    effect.setXOffset(0)
    effect.setYOffset(y_offset)
    color = QColor(pal.shadow)
    color.setAlpha(pal.shadow_strength)
    effect.setColor(color)
    widget.setGraphicsEffect(effect)
    return effect


# ── Text helpers ────────────────────────────────────────────────────


def label(
    text: str,
    role: str = "body",
    tone: str | None = None,
    wrap: bool = False,
    parent: QWidget | None = None,
) -> QLabel:
    """Create a label bound to a typography role from the design system."""
    lbl = QLabel(text, parent)
    lbl.setProperty("role", role)
    if tone:
        lbl.setProperty("tone", tone)
    lbl.setWordWrap(wrap)
    return lbl


class Badge(QLabel):
    """Small pill used for status and metadata."""

    def __init__(
        self,
        text: str,
        variant: str = "neutral",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(text, parent)
        self.setProperty("badge", variant)
        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def set_variant(self, variant: str) -> None:
        self.setProperty("badge", variant)
        repolish(self)

    def set_content(self, text: str, variant: str | None = None) -> None:
        self.setText(text)
        if variant:
            self.set_variant(variant)


# ── Buttons ─────────────────────────────────────────────────────────


class Button(QPushButton, Themed):
    """A themed push button with an optional leading icon."""

    def __init__(
        self,
        text: str = "",
        icon: str | None = None,
        role: str = "default",
        tone: str = "auto",
        height: int = SIZE.control_height,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(text, parent)
        self._icon_name = icon
        self._icon_tone = tone
        self.setProperty("role", role)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(height)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._register_theme()

    def set_icon_name(self, name: str | None) -> None:
        self._icon_name = name
        self.apply_theme(palette())

    def apply_theme(self, p: ColorPalette) -> None:
        if not self._icon_name:
            return
        role = self.property("role")
        if self._icon_tone != "auto":
            color = getattr(p, self._icon_tone, p.text_secondary)
        elif role == "primary":
            color = p.text_inverse
        elif role in {"secondary", "link"}:
            color = p.primary
        elif role == "danger":
            color = p.error
        else:
            color = p.text_secondary
        self.setIcon(get_icon(self._icon_name, color, SIZE.icon_md))


class IconButton(QPushButton, Themed):
    """A square, icon-only button (close, edit, remove, …)."""

    def __init__(
        self,
        icon: str,
        tooltip: str = "",
        size: int = 30,
        icon_size: int = SIZE.icon_md,
        tone: str = "text_secondary",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._icon_name = icon
        self._icon_px = icon_size
        self._tone = tone
        self.setProperty("role", "iconOnly")
        self.setFixedSize(size, size)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        if tooltip:
            self.setToolTip(tooltip)
            self.setAccessibleName(tooltip)
        self._register_theme()

    def set_tone(self, tone: str) -> None:
        self._tone = tone
        self.apply_theme(palette())

    def apply_theme(self, p: ColorPalette) -> None:
        color = getattr(p, self._tone, p.text_secondary)
        self.setIcon(get_icon(self._icon_name, color, self._icon_px))


class ChipButton(QPushButton, Themed):
    """A pill-shaped toggle used for quick choices."""

    def __init__(
        self,
        text: str,
        icon: str | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(text, parent)
        self._icon_name = icon
        self.setProperty("role", "chip")
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(SIZE.control_height_sm)
        self.toggled.connect(self._on_toggled)
        self._register_theme()

    def _on_toggled(self, checked: bool) -> None:
        self.setProperty("active", "true" if checked else "false")
        repolish(self)
        self.apply_theme(palette())

    def apply_theme(self, p: ColorPalette) -> None:
        if not self._icon_name:
            return
        color = p.primary if self.isChecked() else p.text_secondary
        self.setIcon(get_icon(self._icon_name, color, SIZE.icon_sm))


# ── Containers ──────────────────────────────────────────────────────


class Card(QFrame):
    """A rounded surface with a soft border and optional elevation."""

    def __init__(
        self,
        padding: int = SPACE.xl,
        spacing: int = SPACE.md,
        elevated: bool = False,
        variant: str = "card",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setProperty("role", variant)
        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(padding, padding, padding, padding)
        self.body.setSpacing(spacing)
        if elevated:
            apply_shadow(self, blur=28, y_offset=6)

    def add(self, widget: QWidget, stretch: int = 0) -> QWidget:
        self.body.addWidget(widget, stretch)
        return widget

    def add_layout(self, layout, stretch: int = 0):
        self.body.addLayout(layout, stretch)
        return layout


class SectionHeader(QWidget, Themed):
    """Icon + title (+ subtitle) with an optional trailing widget slot."""

    def __init__(
        self,
        title: str,
        icon: str | None = None,
        subtitle: str = "",
        title_role: str = "cardTitle",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._icon_name = icon

        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(SPACE.sm)

        self._icon_lbl: QLabel | None = None
        if icon:
            self._icon_lbl = icon_label(icon, palette().primary, SIZE.icon_lg)
            row.addWidget(self._icon_lbl, 0, Qt.AlignmentFlag.AlignVCenter)

        text_col = QVBoxLayout()
        text_col.setContentsMargins(0, 0, 0, 0)
        text_col.setSpacing(1)
        text_col.addWidget(label(title, title_role))
        if subtitle:
            text_col.addWidget(label(subtitle, "caption", wrap=True))
        # The text column takes the free width so subtitles wrap across
        # the card rather than into a narrow ribbon.
        row.addLayout(text_col, 1)

        self._trailing_slot = row
        self._register_theme()

    def add_trailing(self, widget: QWidget) -> QWidget:
        self._trailing_slot.addWidget(widget)
        return widget

    def apply_theme(self, p: ColorPalette) -> None:
        if self._icon_lbl is not None and self._icon_name:
            self._icon_lbl.setPixmap(
                get_pixmap(self._icon_name, p.primary, SIZE.icon_lg)
            )


class StatCard(Card, Themed):
    """A compact metric tile: icon, caption, value, optional hint."""

    def __init__(
        self,
        caption: str,
        value: str,
        icon: str = Icon.DOT,
        tone: str = "primary",
        hint: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(padding=SPACE.lg, spacing=SPACE.sm, parent=parent)
        self._icon_name = icon
        self._tone = tone

        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)
        top.setSpacing(SPACE.sm)
        self._icon_lbl = icon_label(icon, getattr(palette(), tone), SIZE.icon_md)
        top.addWidget(self._icon_lbl)
        top.addWidget(label(caption, "caption"))
        top.addStretch()
        self.add_layout(top)

        self._value_lbl = label(value, "stat")
        self.add(self._value_lbl)

        self._hint_lbl = label(hint, "caption", wrap=True)
        self._hint_lbl.setVisible(bool(hint))
        self.add(self._hint_lbl)

        self._register_theme()

    def set_value(self, value: str, hint: str = "") -> None:
        self._value_lbl.setText(value)
        self._hint_lbl.setText(hint)
        self._hint_lbl.setVisible(bool(hint))

    def apply_theme(self, p: ColorPalette) -> None:
        self._icon_lbl.setPixmap(
            get_pixmap(self._icon_name, getattr(p, self._tone, p.primary), SIZE.icon_md)
        )


class InfoNote(QFrame, Themed):
    """A small inline banner used for reassurance and validation."""

    def __init__(
        self,
        text: str,
        variant: str = "info",
        icon: str | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._variant = variant
        self._icon_name = icon or _VARIANT_ICONS.get(variant, Icon.INFO)
        self.setProperty("banner", variant)

        row = QHBoxLayout(self)
        row.setContentsMargins(SPACE.md, SPACE.sm + 1, SPACE.md, SPACE.sm + 1)
        row.setSpacing(SPACE.sm)

        self._icon_lbl = icon_label(self._icon_name, self._tone_color(), SIZE.icon_md)
        row.addWidget(self._icon_lbl, 0, Qt.AlignmentFlag.AlignTop)

        self._text_lbl = QLabel(text)
        self._text_lbl.setWordWrap(True)
        row.addWidget(self._text_lbl, 1)

        self._register_theme()

    def _tone_color(self) -> str:
        return getattr(palette(), self._variant, palette().info)

    def set_message(self, text: str, variant: str | None = None) -> None:
        self._text_lbl.setText(text)
        if variant and variant != self._variant:
            self._variant = variant
            self._icon_name = _VARIANT_ICONS.get(variant, Icon.INFO)
            self.setProperty("banner", variant)
            repolish(self)
        self.apply_theme(palette())

    def apply_theme(self, p: ColorPalette) -> None:
        color = getattr(p, self._variant, p.info)
        self._icon_lbl.setPixmap(get_pixmap(self._icon_name, color, SIZE.icon_md))


_VARIANT_ICONS = {
    "info": Icon.INFO,
    "success": Icon.SUCCESS,
    "warning": Icon.WARNING,
    "error": Icon.ERROR,
}


class EmptyState(QWidget, Themed):
    """Centred illustration + copy shown when a list has no content."""

    def __init__(
        self,
        icon: str,
        title: str,
        description: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._icon_name = icon

        col = QVBoxLayout(self)
        col.setContentsMargins(SPACE.xl, SPACE.xxl, SPACE.xl, SPACE.xxl)
        col.setSpacing(SPACE.sm)
        col.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._icon_lbl = icon_label(icon, palette().text_tertiary, 34)
        col.addWidget(self._icon_lbl, 0, Qt.AlignmentFlag.AlignHCenter)

        title_lbl = label(title, "cardTitle")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        col.addWidget(title_lbl)

        if description:
            desc = label(description, "caption", wrap=True)
            desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
            desc.setMaximumWidth(420)
            col.addWidget(desc, 0, Qt.AlignmentFlag.AlignHCenter)

        self._actions = QHBoxLayout()
        self._actions.setSpacing(SPACE.sm)
        self._actions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        col.addSpacing(SPACE.xs)
        col.addLayout(self._actions)

        self._register_theme()

    def add_action(self, widget: QWidget) -> QWidget:
        self._actions.addWidget(widget)
        return widget

    def apply_theme(self, p: ColorPalette) -> None:
        self._icon_lbl.setPixmap(get_pixmap(self._icon_name, p.text_tertiary, 34))


class StepIndicator(QWidget):
    """Horizontal breadcrumb showing where the user is in the workflow."""

    def __init__(self, steps: Iterable[str], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._steps = list(steps)
        self._pills: list[QLabel] = []
        self._seps: list[QLabel] = []
        # Never let the pills shrink into unreadable initials; a caller
        # short on room should hide the whole indicator instead.
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)

        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(SPACE.xs)

        for index, name in enumerate(self._steps):
            if index:
                sep = QLabel("·")
                sep.setProperty("role", "caption")
                row.addWidget(sep)
                self._seps.append(sep)
            pill = QLabel(name)
            pill.setProperty("step", "todo")
            row.addWidget(pill)
            self._pills.append(pill)

        row.addStretch()
        self.set_current(0)

    def set_current(self, index: int) -> None:
        for i, pill in enumerate(self._pills):
            state = "done" if i < index else ("current" if i == index else "todo")
            pill.setProperty("step", state)
            repolish(pill)


class FieldRow(QWidget):
    """A labelled form row: caption above, control below."""

    def __init__(
        self,
        caption: str,
        control: QWidget,
        hint: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        col = QVBoxLayout(self)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(SPACE.xs + 2)
        col.addWidget(label(caption.upper(), "eyebrow"))
        col.addWidget(control)
        if hint:
            col.addWidget(label(hint, "caption", wrap=True))
        self.control = control


def clear_layout(layout) -> None:
    """Remove and destroy every widget in *layout*.

    Detaching before ``deleteLater`` matters: a widget queued for
    deletion is still a child until the event loop runs, and would keep
    painting over whatever replaces it.
    """
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
            widget.setParent(None)
            widget.deleteLater()
        elif item.layout() is not None:
            clear_layout(item.layout())


def horizontal_rule(parent: QWidget | None = None) -> QFrame:
    """A one-pixel separator line."""
    line = QFrame(parent)
    line.setProperty("role", "separator")
    line.setFrameShape(QFrame.Shape.HLine)
    return line


def scroll_container(
    content: QWidget,
    margins: tuple[int, int, int, int] = (0, 0, 0, 0),
):
    """Wrap *content* in a frameless, transparent, vertical scroll area."""
    from PySide6.QtWidgets import QScrollArea

    area = QScrollArea()
    area.setWidgetResizable(True)
    area.setFrameShape(QFrame.Shape.NoFrame)
    area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    area.setViewportMargins(*margins)
    area.setWidget(content)
    area.viewport().setAutoFillBackground(False)
    content.setAutoFillBackground(False)
    return area


def centered_page(
    content: QWidget,
    max_width: int = SIZE.content_max_width,
    margins: tuple[int, int, int, int] = (SPACE.xxxl, SPACE.xxl, SPACE.xxxl, SPACE.xxl),
) -> QWidget:
    """Centre *content* horizontally and cap its width.

    Keeps the layout comfortable on 4K displays without letting the
    interface stretch into a web page.
    """
    wrapper = QWidget()
    wrapper.setObjectName("pageRoot")
    outer = QHBoxLayout(wrapper)
    outer.setContentsMargins(*margins)
    outer.setSpacing(0)
    content.setMaximumWidth(max_width)
    outer.addStretch(1)
    outer.addWidget(content, 10)
    outer.addStretch(1)
    return wrapper


def fade_in(widget: QWidget, duration: int = 160) -> QPropertyAnimation:
    """Animate *widget*'s window opacity from transparent to opaque."""
    widget.setWindowOpacity(0.0)
    anim = QPropertyAnimation(widget, b"windowOpacity", widget)
    anim.setDuration(duration)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(QEasingCurve.Type.OutCubic)
    anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
    return anim


class ClickableCard(Card):
    """A card that behaves like a button."""

    clicked = Signal()

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setProperty("interactive", "true")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self.rect().contains(
            event.position().toPoint()
        ):
            self.clicked.emit()
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event) -> None:
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
            self.clicked.emit()
            return
        super().keyPressEvent(event)


def connect_action(button: QPushButton, handler: Callable[[], None]) -> QPushButton:
    """Wire a zero-argument handler to a button and return the button."""
    button.clicked.connect(lambda: handler())
    return button
