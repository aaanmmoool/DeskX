"""Spacing, radius, and sizing tokens.

Layout numbers live here so every screen breathes the same way.  Use
``SPACE.md`` rather than typing ``12`` into a layout call.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Spacing:
    """Spacing scale in pixels (4px base grid)."""

    xxs: int = 2
    xs: int = 4
    sm: int = 8
    md: int = 12
    lg: int = 16
    xl: int = 20
    xxl: int = 24
    xxxl: int = 32
    huge: int = 40


@dataclass(frozen=True)
class Radius:
    """Corner radii in pixels."""

    xs: int = 6
    sm: int = 8
    md: int = 10
    lg: int = 14
    xl: int = 18
    pill: int = 999


@dataclass(frozen=True)
class Sizing:
    """Fixed control dimensions shared across screens."""

    sidebar_width: int = 236
    control_height: int = 34
    control_height_lg: int = 40
    control_height_sm: int = 28
    icon_sm: int = 14
    icon_md: int = 16
    icon_lg: int = 18
    icon_xl: int = 22

    # Content is centred and capped so the app never looks like a
    # stretched web page on ultrawide monitors.
    content_max_width: int = 1180

    # Modal dialogs must fit comfortably on a 1366x768 display.
    modal_max_height: int = 660


SPACE = Spacing()
RADIUS = Radius()
SIZE = Sizing()
