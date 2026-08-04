"""Colour palettes for dark and light themes.

Each palette is a plain dataclass so the stylesheet generator can
access tokens by name without string parsing.

The colours are inspired by Linear / Notion — muted, desaturated
tones with high contrast where it matters.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class ThemeMode(Enum):
    DARK = auto()
    LIGHT = auto()


@dataclass(frozen=True)
class ColorPalette:
    """Complete set of semantic colour tokens."""

    # ── Surfaces ────────────────────────────────────────────────────
    bg_primary: str       # main window background
    bg_secondary: str     # cards, panels
    bg_tertiary: str      # nav rail, subtle sections
    bg_elevated: str      # modals, tooltips
    bg_hover: str         # interactive hover state
    bg_active: str        # pressed / selected state

    # ── Borders ─────────────────────────────────────────────────────
    border_subtle: str    # card outlines
    border_default: str   # inputs
    border_strong: str    # focus rings

    # ── Text ────────────────────────────────────────────────────────
    text_primary: str     # headings, body
    text_secondary: str   # captions, labels
    text_tertiary: str    # placeholders, disabled
    text_inverse: str     # text on accent buttons

    # ── Accent ──────────────────────────────────────────────────────
    accent: str           # primary CTA
    accent_hover: str
    accent_subtle: str    # light tint behind badges

    # ── Semantic ────────────────────────────────────────────────────
    success: str
    warning: str
    error: str
    info: str

    # ── Drag-and-drop ───────────────────────────────────────────────
    drop_zone_border: str
    drop_zone_bg: str
    drop_zone_active_border: str
    drop_zone_active_bg: str

    # ── Scrollbar ───────────────────────────────────────────────────
    scrollbar_bg: str
    scrollbar_handle: str
    scrollbar_handle_hover: str

    # ── Table ───────────────────────────────────────────────────────
    table_header_bg: str
    table_row_alt: str
    table_selection: str


# ── Palettes ────────────────────────────────────────────────────────

DARK = ColorPalette(
    # Surfaces
    bg_primary="#0F1117",
    bg_secondary="#16181D",
    bg_tertiary="#1C1E26",
    bg_elevated="#22252E",
    bg_hover="#282B35",
    bg_active="#2E3240",

    # Borders
    border_subtle="#262933",
    border_default="#353845",
    border_strong="#505466",

    # Text
    text_primary="#EDEEF0",
    text_secondary="#9B9FAD",
    text_tertiary="#6B6F7E",
    text_inverse="#0F1117",

    # Accent — soft indigo-blue
    accent="#6C72CB",
    accent_hover="#8186D8",
    accent_subtle="rgba(108, 114, 203, 0.15)",

    # Semantic
    success="#34D399",
    warning="#FBBF24",
    error="#F87171",
    info="#60A5FA",

    # Drag-and-drop
    drop_zone_border="#353845",
    drop_zone_bg="#16181D",
    drop_zone_active_border="#6C72CB",
    drop_zone_active_bg="rgba(108, 114, 203, 0.08)",

    # Scrollbar
    scrollbar_bg="transparent",
    scrollbar_handle="#353845",
    scrollbar_handle_hover="#505466",

    # Table
    table_header_bg="#1C1E26",
    table_row_alt="#16181D",
    table_selection="rgba(108, 114, 203, 0.20)",
)

LIGHT = ColorPalette(
    # Surfaces
    bg_primary="#FFFFFF",
    bg_secondary="#F8F9FA",
    bg_tertiary="#F1F3F5",
    bg_elevated="#FFFFFF",
    bg_hover="#E9ECEF",
    bg_active="#DEE2E6",

    # Borders
    border_subtle="#E9ECEF",
    border_default="#CED4DA",
    border_strong="#ADB5BD",

    # Text
    text_primary="#1A1A2E",
    text_secondary="#6C757D",
    text_tertiary="#ADB5BD",
    text_inverse="#FFFFFF",

    # Accent — soft indigo-blue
    accent="#5B5FC7",
    accent_hover="#4B4FB7",
    accent_subtle="rgba(91, 95, 199, 0.10)",

    # Semantic
    success="#10B981",
    warning="#F59E0B",
    error="#EF4444",
    info="#3B82F6",

    # Drag-and-drop
    drop_zone_border="#CED4DA",
    drop_zone_bg="#F8F9FA",
    drop_zone_active_border="#5B5FC7",
    drop_zone_active_bg="rgba(91, 95, 199, 0.06)",

    # Scrollbar
    scrollbar_bg="transparent",
    scrollbar_handle="#CED4DA",
    scrollbar_handle_hover="#ADB5BD",

    # Table
    table_header_bg="#F1F3F5",
    table_row_alt="#F8F9FA",
    table_selection="rgba(91, 95, 199, 0.12)",
)


def get_palette(mode: ThemeMode) -> ColorPalette:
    """Return the palette for the requested theme mode."""
    return DARK if mode is ThemeMode.DARK else LIGHT
