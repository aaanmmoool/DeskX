"""Typography tokens.

A single, deliberately small type scale.  Anything that needs a size
should pick the nearest role below rather than inventing a new number,
so headings stay consistent between screens.

Roles
-----
``size_display``  application-level hero heading (Home greeting)
``size_3xl``      page heading
``size_2xl``      large numeric / stat value
``size_xl``       section heading
``size_lg``       card title, prominent body
``size_md``       body text (default)
``size_sm``       supporting text
``size_xs``       captions, eyebrow labels, badges
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FontTokens:
    """Typography design tokens."""

    family: str = "'Segoe UI Variable Text', 'Segoe UI', 'Inter', -apple-system, sans-serif"
    family_display: str = (
        "'Segoe UI Variable Display', 'Segoe UI Semibold', 'Segoe UI', 'Inter', sans-serif"
    )
    family_mono: str = "'Cascadia Mono', 'Consolas', 'JetBrains Mono', monospace"

    # Sizes (px)
    size_xs: int = 11
    size_sm: int = 12
    size_md: int = 13
    size_lg: int = 15
    size_xl: int = 17
    size_2xl: int = 21
    size_3xl: int = 25
    size_display: int = 30

    # Weights
    weight_normal: int = 400
    weight_medium: int = 500
    weight_semibold: int = 600
    weight_bold: int = 700

    # Line height factor
    line_height: float = 1.5


FONTS = FontTokens()
