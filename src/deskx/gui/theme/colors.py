"""Colour palettes for the DeskX design system.

Every colour used anywhere in the GUI comes from one of the two
palettes defined here.  Widgets must never hard-code a hex value —
they should read a token from :func:`get_palette` (or, preferably,
let the generated stylesheet do it for them).

The light palette is the canonical DeskX identity: a near-white
canvas, pure-white cards, indigo/violet primary, and a teal secondary
used sparingly for highlights.
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
    bg_primary: str       # app canvas
    bg_secondary: str     # cards / panels
    bg_tertiary: str      # subtle fills, inset sections
    bg_elevated: str      # modals, popovers, tooltips
    bg_hover: str         # interactive hover state
    bg_active: str        # pressed / selected state
    bg_sidebar: str       # navigation rail

    # ── Borders ─────────────────────────────────────────────────────
    border_subtle: str    # card outlines
    border_default: str   # inputs
    border_strong: str    # emphasised outlines

    # ── Text ────────────────────────────────────────────────────────
    text_primary: str     # headings, body
    text_secondary: str   # supporting copy
    text_tertiary: str    # placeholders, disabled
    text_muted: str       # eyebrow labels, captions
    text_inverse: str     # text on filled accent surfaces

    # ── Brand ───────────────────────────────────────────────────────
    primary: str
    primary_hover: str
    primary_pressed: str
    primary_subtle: str   # tinted background behind badges / selection
    primary_border: str

    secondary: str
    secondary_subtle: str

    # ``accent`` is kept as an alias of ``primary`` so existing code and
    # stylesheet rules that reference it keep working.
    accent: str
    accent_hover: str
    accent_subtle: str

    # ── Semantic ────────────────────────────────────────────────────
    success: str
    success_subtle: str
    warning: str
    warning_subtle: str
    error: str
    error_subtle: str
    info: str
    info_subtle: str

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
    table_grid: str

    # ── Elevation (QGraphicsDropShadowEffect colour) ────────────────
    shadow: str
    shadow_strength: int  # alpha 0–255

    # ── Misc ────────────────────────────────────────────────────────
    overlay: str          # modal scrim
    is_dark: bool


# ── Light — the canonical DeskX look ────────────────────────────────

LIGHT = ColorPalette(
    bg_primary="#F5F5FA",
    bg_secondary="#FFFFFF",
    bg_tertiary="#F1F1F8",
    bg_elevated="#FFFFFF",
    bg_hover="#F0F0F7",
    bg_active="#E7E7F2",
    bg_sidebar="#FFFFFF",

    border_subtle="#EAEAF2",
    border_default="#DEDEE9",
    border_strong="#C4C4D4",

    text_primary="#14141F",
    text_secondary="#565669",
    text_tertiary="#9494A8",
    text_muted="#7A7A8F",
    text_inverse="#FFFFFF",

    primary="#6C5CE7",
    primary_hover="#5D4DD8",
    primary_pressed="#4F40C4",
    primary_subtle="#EFEDFD",
    primary_border="#D6D0FA",

    secondary="#0FA9A0",
    secondary_subtle="#E3F8F6",

    accent="#6C5CE7",
    accent_hover="#5D4DD8",
    accent_subtle="#EFEDFD",

    success="#0F9D58",
    success_subtle="#E4F6EC",
    warning="#B76E00",
    warning_subtle="#FDF1DF",
    error="#D92D20",
    error_subtle="#FDECEA",
    info="#1E6FD9",
    info_subtle="#E7F0FD",

    drop_zone_border="#D6D0FA",
    drop_zone_bg="#FBFAFF",
    drop_zone_active_border="#6C5CE7",
    drop_zone_active_bg="#F2F0FE",

    scrollbar_bg="transparent",
    scrollbar_handle="#D6D6E2",
    scrollbar_handle_hover="#B9B9CB",

    table_header_bg="#F7F7FC",
    table_row_alt="#FBFBFE",
    table_selection="#EFEDFD",
    table_grid="#EDEDF4",

    shadow="#1A1A3A",
    shadow_strength=28,

    overlay="rgba(20, 20, 31, 0.42)",
    is_dark=False,
)


# ── Dark — same system, inverted surfaces ───────────────────────────

DARK = ColorPalette(
    bg_primary="#0D0D14",
    bg_secondary="#16161F",
    bg_tertiary="#1D1D28",
    bg_elevated="#1F1F2B",
    bg_hover="#25252F",
    bg_active="#2D2D3A",
    bg_sidebar="#111119",

    border_subtle="#262633",
    border_default="#33333F",
    border_strong="#494957",

    text_primary="#EDEDF2",
    text_secondary="#A6A6BA",
    text_tertiary="#6E6E85",
    text_muted="#8A8AA0",
    text_inverse="#FFFFFF",

    primary="#8B7CF6",
    primary_hover="#9C8FF8",
    primary_pressed="#7A6AE8",
    primary_subtle="#211E3A",
    primary_border="#3A3468",

    secondary="#2DD4BF",
    secondary_subtle="#12302F",

    accent="#8B7CF6",
    accent_hover="#9C8FF8",
    accent_subtle="#211E3A",

    success="#34D399",
    success_subtle="#10291F",
    warning="#FBBF24",
    warning_subtle="#2E2410",
    error="#F87171",
    error_subtle="#301818",
    info="#60A5FA",
    info_subtle="#141F33",

    drop_zone_border="#3A3468",
    drop_zone_bg="#14141D",
    drop_zone_active_border="#8B7CF6",
    drop_zone_active_bg="#1B1930",

    scrollbar_bg="transparent",
    scrollbar_handle="#33333F",
    scrollbar_handle_hover="#494957",

    table_header_bg="#1A1A24",
    table_row_alt="#14141D",
    table_selection="#241F45",
    table_grid="#242430",

    shadow="#000000",
    shadow_strength=110,

    overlay="rgba(0, 0, 0, 0.58)",
    is_dark=True,
)


def get_palette(mode: ThemeMode) -> ColorPalette:
    """Return the palette for the requested theme mode."""
    return DARK if mode is ThemeMode.DARK else LIGHT
