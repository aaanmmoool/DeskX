"""Transient toast notifications.

Toasts are non-blocking confirmations that slide in at the bottom of
the window and fade out on their own.  Use them for outcomes the user
already expects (copied, saved, cancelled); anything the user must act
on belongs in an inline banner or a modal instead.
"""

from __future__ import annotations

from PySide6.QtCore import (
    QEasingCurve,
    QPoint,
    QPropertyAnimation,
    QTimer,
    Qt,
)
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QWidget,
)

from deskx.gui.theme import SIZE, SPACE, palette
from deskx.gui.theme.icons import Icon, icon_label
from deskx.gui.widgets.components import apply_shadow

_VARIANT_ICONS = {
    "success": Icon.SUCCESS,
    "error": Icon.ERROR,
    "warning": Icon.WARNING,
    "info": Icon.INFO,
}


class Toast(QFrame):
    """A single floating notification pinned to its parent window."""

    def __init__(
        self,
        parent: QWidget,
        message: str,
        variant: str = "info",
        duration_ms: int = 3200,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("toast")
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)

        pal = palette()
        tone = getattr(pal, variant, pal.info)

        row = QHBoxLayout(self)
        row.setContentsMargins(SPACE.md, SPACE.sm + 2, SPACE.lg, SPACE.sm + 2)
        row.setSpacing(SPACE.sm)
        row.addWidget(icon_label(_VARIANT_ICONS.get(variant, Icon.INFO), tone, SIZE.icon_md))

        text = QLabel(message)
        text.setWordWrap(False)
        row.addWidget(text)

        apply_shadow(self, blur=32, y_offset=8)
        self.adjustSize()

        self._opacity = QGraphicsOpacityEffect(self)
        self._opacity.setOpacity(0.0)
        # A widget can hold only one graphics effect, so the shadow is
        # replaced by the opacity effect used for the fade.
        self.setGraphicsEffect(self._opacity)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._fade_out)
        self._timer.start(duration_ms)

    def show_at_bottom(self, margin: int = SPACE.xxl) -> None:
        """Position above the bottom edge of the parent and animate in."""
        parent = self.parentWidget()
        if parent is None:
            self.show()
            return

        self.adjustSize()
        x = (parent.width() - self.width()) // 2
        y_end = parent.height() - self.height() - margin
        self.move(x, y_end + 14)
        self.show()
        self.raise_()

        slide = QPropertyAnimation(self, b"pos", self)
        slide.setDuration(200)
        slide.setStartValue(QPoint(x, y_end + 14))
        slide.setEndValue(QPoint(x, y_end))
        slide.setEasingCurve(QEasingCurve.Type.OutCubic)
        slide.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)

        fade = QPropertyAnimation(self._opacity, b"opacity", self)
        fade.setDuration(200)
        fade.setStartValue(0.0)
        fade.setEndValue(1.0)
        fade.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
        self._fade_in = fade

    def _fade_out(self) -> None:
        fade = QPropertyAnimation(self._opacity, b"opacity", self)
        fade.setDuration(240)
        fade.setStartValue(self._opacity.opacity())
        fade.setEndValue(0.0)
        fade.setEasingCurve(QEasingCurve.Type.InCubic)
        fade.finished.connect(self.close)
        fade.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
        self._fade_anim = fade


def show_toast(
    parent: QWidget,
    message: str,
    variant: str = "info",
    duration_ms: int = 3200,
) -> Toast:
    """Create, position, and animate a toast inside *parent*."""
    toast = Toast(parent, message, variant, duration_ms)
    toast.show_at_bottom()
    return toast
