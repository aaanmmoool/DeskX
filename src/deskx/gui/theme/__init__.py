"""Theme engine — design tokens, icon set, and stylesheet generation.

The active theme is process-global so any widget can tint an icon to
match the current palette without threading a palette object through
every constructor::

    from deskx.gui.theme import palette
    from deskx.gui.theme.icons import Icon, icon_label

    icon_label(Icon.SHIELD, palette().success, 18)

``MainWindow`` owns the theme and calls :func:`set_mode` when the user
toggles it; widgets that cache tinted pixmaps should implement
``apply_theme()`` and will be called back automatically.
"""

from __future__ import annotations

from typing import Callable

from deskx.gui.theme.colors import ColorPalette, ThemeMode, get_palette
from deskx.gui.theme.fonts import FONTS
from deskx.gui.theme.metrics import RADIUS, SIZE, SPACE

_mode: ThemeMode = ThemeMode.LIGHT
_listeners: list[Callable[[ColorPalette], None]] = []


def mode() -> ThemeMode:
    """Return the currently active theme mode."""
    return _mode


def palette() -> ColorPalette:
    """Return the colour palette for the active theme."""
    return get_palette(_mode)


def set_mode(new_mode: ThemeMode) -> None:
    """Switch the active theme and notify every subscriber."""
    global _mode
    _mode = new_mode
    current = get_palette(_mode)
    for listener in list(_listeners):
        listener(current)


def subscribe(listener: Callable[[ColorPalette], None]) -> None:
    """Register *listener* to be called whenever the theme changes."""
    if listener not in _listeners:
        _listeners.append(listener)


def unsubscribe(listener: Callable[[ColorPalette], None]) -> None:
    """Stop notifying *listener* of theme changes."""
    if listener in _listeners:
        _listeners.remove(listener)


__all__ = [
    "ColorPalette",
    "FONTS",
    "RADIUS",
    "SIZE",
    "SPACE",
    "ThemeMode",
    "mode",
    "palette",
    "set_mode",
    "subscribe",
    "unsubscribe",
]
