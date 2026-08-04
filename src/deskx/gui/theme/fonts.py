"""Typography tokens.

Defines font families, sizes, and weights used across the application.
The primary font is Inter (bundled) with Segoe UI as fallback.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FontTokens:
    """Typography design tokens."""

    family: str = "'Segoe UI', 'Inter', -apple-system, 'Helvetica Neue', sans-serif"

    # Sizes (px)
    size_xs: int = 11
    size_sm: int = 12
    size_md: int = 13
    size_lg: int = 15
    size_xl: int = 18
    size_2xl: int = 22
    size_3xl: int = 28

    # Weights
    weight_normal: int = 400
    weight_medium: int = 500
    weight_semibold: int = 600
    weight_bold: int = 700

    # Line height factor
    line_height: float = 1.5


FONTS = FontTokens()
