"""QSS stylesheet generator.

Builds a complete Qt Style Sheet from the colour palette and font
tokens.  Call :func:`generate_stylesheet` whenever the theme mode
changes, then apply via ``QApplication.setStyleSheet()``.
"""

from __future__ import annotations

from deskx.gui.theme.colors import ColorPalette, ThemeMode, get_palette
from deskx.gui.theme.fonts import FONTS, FontTokens


def generate_stylesheet(mode: ThemeMode) -> str:
    """Return the full QSS for the given *mode*."""
    c = get_palette(mode)
    f = FONTS
    return _build(c, f)


def _build(c: ColorPalette, f: FontTokens) -> str:  # noqa: C901 — long but flat
    """Compose all QSS rules."""
    return f"""
/* ================================================================
   DeskX — Generated Stylesheet
   ================================================================ */

/* ── Global ──────────────────────────────────────────────────── */
* {{
    font-family: {f.family};
    font-size: {f.size_md}px;
    outline: none;
}}

QMainWindow, QWidget#centralWidget {{
    background-color: {c.bg_primary};
    color: {c.text_primary};
}}

/* ── Top bar ─────────────────────────────────────────────────── */
QFrame#topBar {{
    background-color: {c.bg_secondary};
    border-bottom: 1px solid {c.border_subtle};
}}

/* ── Status bar ──────────────────────────────────────────────── */
QFrame#statusBar {{
    background-color: {c.bg_secondary};
    border-top: 1px solid {c.border_subtle};
}}

/* ── Config toolbar ──────────────────────────────────────────── */
QFrame#configToolbar {{
    background-color: {c.bg_secondary};
    border-bottom: 1px solid {c.border_subtle};
}}

/* ── Success / Error banners ─────────────────────────────────── */
QFrame#successBanner {{
    background-color: rgba(52, 211, 153, 0.12);
    border-top: 1px solid {c.success};
}}
QFrame#successBanner QLabel {{
    color: {c.success};
}}

QFrame#errorBanner {{
    background-color: rgba(248, 113, 113, 0.12);
    border-top: 1px solid {c.error};
}}
QFrame#errorBanner QLabel {{
    color: {c.error};
}}

/* ── Scrollbar ───────────────────────────────────────────────── */
QScrollBar:vertical {{
    background: {c.scrollbar_bg};
    width: 8px;
    margin: 0;
    border: none;
    border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: {c.scrollbar_handle};
    min-height: 30px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical:hover {{
    background: {c.scrollbar_handle_hover};
}}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {{
    background: none;
    height: 0px;
    border: none;
}}

QScrollBar:horizontal {{
    background: {c.scrollbar_bg};
    height: 8px;
    margin: 0;
    border: none;
    border-radius: 4px;
}}
QScrollBar::handle:horizontal {{
    background: {c.scrollbar_handle};
    min-width: 30px;
    border-radius: 4px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {c.scrollbar_handle_hover};
}}
QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal,
QScrollBar::add-page:horizontal,
QScrollBar::sub-page:horizontal {{
    background: none;
    width: 0px;
    border: none;
}}

/* ── Labels ──────────────────────────────────────────────────── */
QLabel {{
    color: {c.text_primary};
    background: transparent;
    border: none;
}}
QLabel[role="heading"] {{
    font-size: {f.size_2xl}px;
    font-weight: {f.weight_semibold};
}}
QLabel[role="subheading"] {{
    font-size: {f.size_lg}px;
    font-weight: {f.weight_medium};
    color: {c.text_secondary};
}}
QLabel[role="caption"] {{
    font-size: {f.size_sm}px;
    color: {c.text_tertiary};
}}

/* ── Buttons ─────────────────────────────────────────────────── */
QPushButton {{
    background-color: {c.bg_tertiary};
    color: {c.text_primary};
    border: 1px solid {c.border_subtle};
    border-radius: 8px;
    padding: 8px 20px;
    font-size: {f.size_md}px;
    font-weight: {f.weight_medium};
    min-height: 18px;
}}
QPushButton:hover {{
    background-color: {c.bg_hover};
    border-color: {c.border_default};
}}
QPushButton:pressed {{
    background-color: {c.bg_active};
}}
QPushButton:disabled {{
    color: {c.text_tertiary};
    background-color: {c.bg_secondary};
    border-color: {c.border_subtle};
}}
QPushButton[role="primary"] {{
    background-color: {c.accent};
    color: {c.text_inverse};
    border: 1px solid {c.accent};
    font-weight: 600;
}}
QPushButton[role="primary"]:hover {{
    background-color: {c.accent_hover};
    border-color: {c.accent_hover};
}}
QPushButton[role="primary"]:disabled {{
    background-color: {c.bg_tertiary};
    color: {c.text_tertiary};
    border-color: {c.border_subtle};
}}
QPushButton[role="ghost"] {{
    background: transparent;
    border: none;
    padding: 6px 12px;
    color: {c.text_secondary};
}}
QPushButton[role="ghost"]:hover {{
    background-color: {c.bg_hover};
    color: {c.text_primary};
    border-radius: 6px;
}}

/* ── Line edits ──────────────────────────────────────────────── */
QLineEdit {{
    background-color: {c.bg_secondary};
    color: {c.text_primary};
    border: 1px solid {c.border_default};
    border-radius: 8px;
    padding: 8px 12px;
    font-size: {f.size_md}px;
    selection-background-color: {c.accent_subtle};
}}
QLineEdit:focus {{
    border-color: {c.accent};
}}
QLineEdit:disabled {{
    color: {c.text_tertiary};
}}

/* ── Combo boxes ─────────────────────────────────────────────── */
QComboBox {{
    background-color: {c.bg_secondary};
    color: {c.text_primary};
    border: 1px solid {c.border_default};
    border-radius: 6px;
    padding: 5px 10px;
    font-size: {f.size_sm}px;
    min-height: 18px;
}}
QComboBox:hover {{
    border-color: {c.accent};
}}
QComboBox::drop-down {{
    border: none;
    width: 22px;
    padding-right: 6px;
}}
QComboBox::down-arrow {{
    image: none;
    border: none;
    width: 0; height: 0;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 4px solid {c.text_secondary};
}}
QComboBox QAbstractItemView {{
    background-color: {c.bg_elevated};
    color: {c.text_primary};
    border: 1px solid {c.border_subtle};
    border-radius: 6px;
    padding: 4px;
    selection-background-color: {c.accent_subtle};
    selection-color: {c.text_primary};
}}

/* ── Spin boxes ──────────────────────────────────────────────── */
QSpinBox {{
    background-color: {c.bg_secondary};
    color: {c.text_primary};
    border: 1px solid {c.border_default};
    border-radius: 6px;
    padding: 3px 6px;
    font-size: {f.size_sm}px;
}}
QSpinBox:focus {{
    border-color: {c.accent};
}}
QSpinBox::up-button, QSpinBox::down-button {{
    background: {c.bg_tertiary};
    border: none;
    width: 14px;
}}
QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
    background: {c.bg_hover};
}}

/* ── Radio buttons ───────────────────────────────────────────── */
QRadioButton {{
    color: {c.text_primary};
    spacing: 5px;
    font-size: {f.size_sm}px;
}}
QRadioButton::indicator {{
    width: 14px;
    height: 14px;
    border-radius: 7px;
    border: 2px solid {c.border_default};
    background-color: {c.bg_secondary};
}}
QRadioButton::indicator:hover {{
    border-color: {c.accent};
}}
QRadioButton::indicator:checked {{
    background-color: {c.accent};
    border-color: {c.accent};
}}

/* ── Text edits ──────────────────────────────────────────────── */
QTextEdit {{
    background-color: {c.bg_secondary};
    color: {c.text_primary};
    border: 1px solid {c.border_subtle};
    border-radius: 10px;
    padding: 12px;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: {f.size_sm}px;
    selection-background-color: {c.accent_subtle};
}}

/* ── Table view ──────────────────────────────────────────────── */
QTableView {{
    background-color: {c.bg_primary};
    alternate-background-color: {c.table_row_alt};
    color: {c.text_primary};
    border: 1px solid {c.border_subtle};
    border-radius: 10px;
    gridline-color: {c.border_subtle};
    selection-background-color: {c.table_selection};
    selection-color: {c.text_primary};
    font-size: {f.size_sm}px;
}}
QTableView::item {{
    padding: 5px 8px;
    border: none;
}}
QTableView::item:selected {{
    background-color: {c.table_selection};
}}
QHeaderView::section {{
    background-color: {c.table_header_bg};
    color: {c.text_secondary};
    font-size: {f.size_xs}px;
    font-weight: {f.weight_semibold};
    padding: 6px 8px;
    border: none;
    border-bottom: 1px solid {c.border_subtle};
    border-right: 1px solid {c.border_subtle};
}}
QHeaderView::section:last {{
    border-right: none;
}}

/* ── Check boxes ─────────────────────────────────────────────── */
QCheckBox {{
    color: {c.text_primary};
    spacing: 6px;
    font-size: {f.size_sm}px;
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 2px solid {c.border_default};
    background-color: {c.bg_secondary};
}}
QCheckBox::indicator:hover {{
    border-color: {c.accent};
}}
QCheckBox::indicator:checked {{
    background-color: {c.accent};
    border-color: {c.accent};
    image: none;
}}

/* ── Progress bar ────────────────────────────────────────────── */
QProgressBar {{
    background-color: {c.bg_tertiary};
    border: none;
    border-radius: 4px;
    text-align: center;
    color: {c.text_secondary};
    font-size: {f.size_xs}px;
    min-height: 8px;
    max-height: 8px;
}}
QProgressBar::chunk {{
    background-color: {c.accent};
    border-radius: 4px;
}}

/* ── Tooltips ────────────────────────────────────────────────── */
QToolTip {{
    background-color: {c.bg_elevated};
    color: {c.text_primary};
    border: 1px solid {c.border_default};
    border-radius: 8px;
    padding: 8px 12px;
    font-size: {f.size_sm}px;
}}

/* ── Dialogs & Modals ────────────────────────────────────────── */
QDialog {{
    background-color: {c.bg_primary};
    color: {c.text_primary};
}}

/* ── Menus ───────────────────────────────────────────────────── */
QMenu {{
    background-color: {c.bg_elevated};
    color: {c.text_primary};
    border: 1px solid {c.border_default};
    border-radius: 8px;
    padding: 6px 4px;
}}
QMenu::item {{
    padding: 8px 24px 8px 12px;
    border-radius: 6px;
    margin: 2px 4px;
}}
QMenu::item:selected {{
    background-color: {c.accent_subtle};
    color: {c.text_primary};
}}
QMenu::separator {{
    height: 1px;
    background: {c.border_subtle};
    margin: 4px 8px;
}}

/* ── Group Boxes ─────────────────────────────────────────────── */
QGroupBox {{
    border: 1px solid {c.border_subtle};
    border-radius: 8px;
    margin-top: 14px;
    padding-top: 10px;
    font-weight: 600;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 6px;
    color: {c.text_secondary};
}}

/* ── Cards ───────────────────────────────────────────────────── */
QFrame[role="card"] {{
    background-color: {c.bg_secondary};
    border: 1px solid {c.border_subtle};
    border-radius: 12px;
}}

/* ── Drag-drop zone ──────────────────────────────────────────── */
QFrame#dropZone {{
    background-color: {c.drop_zone_bg};
    border: 2px dashed {c.drop_zone_border};
    border-radius: 16px;
}}
QFrame#dropZone[dragActive="true"] {{
    border-color: {c.drop_zone_active_border};
    background-color: {c.drop_zone_active_bg};
}}

/* ── Stacked widget pages ────────────────────────────────────── */
QStackedWidget {{
    background-color: {c.bg_primary};
}}

/* ── Separator ───────────────────────────────────────────────── */
QFrame[role="separator"] {{
    background-color: {c.border_subtle};
    max-height: 1px;
    min-height: 1px;
    border: none;
}}

/* ── List widget (recent files) ──────────────────────────────── */
QListWidget {{
    background-color: transparent;
    border: none;
    color: {c.text_primary};
    font-size: {f.size_md}px;
    outline: none;
}}
QListWidget::item {{
    padding: 8px 12px;
    border-radius: 8px;
    border: none;
}}
QListWidget::item:hover {{
    background-color: {c.bg_hover};
}}
QListWidget::item:selected {{
    background-color: {c.table_selection};
    color: {c.text_primary};
}}

/* ── Nav bar (kept for compat but not used) ──────────────────── */
QWidget#navBar {{
    background-color: {c.bg_tertiary};
    border-right: 1px solid {c.border_subtle};
}}
"""


