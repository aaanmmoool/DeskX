"""QSS stylesheet generator.

Builds the complete Qt Style Sheet for DeskX from the colour, type,
and metric tokens.  Call :func:`generate_stylesheet` whenever the
theme mode changes, then apply it via ``QApplication.setStyleSheet()``.

Styling contract
----------------
Widgets opt into a look by setting a dynamic property, never by
calling ``setStyleSheet`` themselves:

``role``    ``primary`` | ``secondary`` | ``ghost`` | ``danger`` |
            ``link`` | ``chip`` | ``iconOnly`` on buttons;
            ``card`` | ``cardFlat`` | ``inset`` | ``separator`` on frames;
            ``display`` | ``pageTitle`` | ``sectionTitle`` | ``cardTitle`` |
            ``body`` | ``caption`` | ``eyebrow`` | ``stat`` | ``mono`` on labels
``badge``   ``neutral`` | ``primary`` | ``success`` | ``warning`` | ``error`` | ``info``
``banner``  ``success`` | ``warning`` | ``error`` | ``info``
``active``  ``true`` on selected nav items / chips

After changing a dynamic property at runtime, call
:func:`repolish` so Qt re-evaluates the rules.
"""

from __future__ import annotations

from PySide6.QtWidgets import QWidget

from deskx.gui.theme.colors import ColorPalette, ThemeMode, get_palette
from deskx.gui.theme.fonts import FONTS, FontTokens
from deskx.gui.theme.icons import Icon, icon_file
from deskx.gui.theme.metrics import RADIUS, SIZE


def generate_stylesheet(mode: ThemeMode) -> str:
    """Return the full QSS for the given *mode*."""
    return _build(get_palette(mode), FONTS)


def repolish(widget: QWidget) -> None:
    """Re-apply the stylesheet to *widget* after a property change."""
    style = widget.style()
    style.unpolish(widget)
    style.polish(widget)
    widget.update()


def _build(c: ColorPalette, f: FontTokens) -> str:
    check = icon_file(Icon.CHECK, c.text_inverse, 12)
    chevron = icon_file(Icon.CHEVRON_DOWN, c.text_secondary, 12)
    up = icon_file(Icon.CHEVRON_DOWN, c.text_secondary, 9)

    return f"""
/* ================================================================
   DeskX — generated stylesheet
   ================================================================ */

* {{
    font-family: {f.family};
    font-size: {f.size_md}px;
    outline: none;
}}

QMainWindow, QWidget#centralWidget {{
    background-color: {c.bg_primary};
    color: {c.text_primary};
}}

QStackedWidget, QWidget#pageRoot {{
    background-color: {c.bg_primary};
}}

/* ── Navigation rail ─────────────────────────────────────────── */
QWidget#sidebar {{
    background-color: {c.bg_sidebar};
    border-right: 1px solid {c.border_subtle};
}}
QWidget#sidebar QLabel {{
    background: transparent;
}}
QLabel#brandName {{
    font-family: {f.family_display};
    font-size: {f.size_xl}px;
    font-weight: {f.weight_bold};
    color: {c.text_primary};
}}
QLabel#brandTag {{
    font-size: {f.size_xs}px;
    color: {c.text_tertiary};
}}
QLabel#navSectionLabel {{
    font-size: {f.size_xs}px;
    font-weight: {f.weight_semibold};
    color: {c.text_tertiary};
    padding: 0 4px;
}}
QPushButton[nav="true"] {{
    background: transparent;
    border: none;
    border-radius: {RADIUS.md}px;
    color: {c.text_secondary};
    font-size: {f.size_md}px;
    font-weight: {f.weight_medium};
    text-align: left;
    padding: 0 10px;
    min-height: 36px;
}}
QPushButton[nav="true"]:hover {{
    background-color: {c.bg_hover};
    color: {c.text_primary};
}}
QPushButton[nav="true"]:focus {{
    border: 1px solid {c.primary_border};
}}
QPushButton[nav="true"][active="true"] {{
    background-color: {c.primary_subtle};
    color: {c.primary};
    font-weight: {f.weight_semibold};
}}
QPushButton[nav="true"]:disabled {{
    color: {c.text_tertiary};
    background: transparent;
}}

/* ── Top bar ─────────────────────────────────────────────────── */
QFrame#topBar {{
    background-color: {c.bg_secondary};
    border-bottom: 1px solid {c.border_subtle};
}}
QFrame#statusBar {{
    background-color: {c.bg_secondary};
    border-top: 1px solid {c.border_subtle};
}}

/* ── Cards ───────────────────────────────────────────────────── */
QFrame[role="card"] {{
    background-color: {c.bg_secondary};
    border: 1px solid {c.border_subtle};
    border-radius: {RADIUS.lg}px;
}}
QFrame[role="card"][interactive="true"]:hover {{
    border-color: {c.primary_border};
    background-color: {c.bg_secondary};
}}
QFrame[role="card"][selected="true"] {{
    border-color: {c.primary};
    background-color: {c.primary_subtle};
}}
QFrame[role="cardFlat"] {{
    background-color: {c.bg_tertiary};
    border: 1px solid transparent;
    border-radius: {RADIUS.md}px;
}}
QFrame[role="inset"] {{
    background-color: {c.bg_tertiary};
    border: 1px solid {c.border_subtle};
    border-radius: {RADIUS.md}px;
}}
QFrame[role="accentCard"] {{
    background-color: {c.primary_subtle};
    border: 1px solid {c.primary_border};
    border-radius: {RADIUS.lg}px;
}}
QFrame[role="separator"] {{
    background-color: {c.border_subtle};
    max-height: 1px;
    min-height: 1px;
    border: none;
}}
QFrame[role="vseparator"] {{
    background-color: {c.border_subtle};
    max-width: 1px;
    min-width: 1px;
    border: none;
}}

/* ── Typography ──────────────────────────────────────────────── */
QLabel {{
    color: {c.text_primary};
    background: transparent;
    border: none;
}}
QLabel[role="display"] {{
    font-family: {f.family_display};
    font-size: {f.size_display}px;
    font-weight: {f.weight_bold};
    color: {c.text_primary};
}}
QLabel[role="displayAccent"] {{
    font-family: {f.family_display};
    font-size: {f.size_display}px;
    font-weight: {f.weight_bold};
    color: {c.secondary};
}}
QLabel[role="pageTitle"] {{
    font-family: {f.family_display};
    font-size: {f.size_3xl}px;
    font-weight: {f.weight_semibold};
}}
QLabel[role="heading"] {{
    font-size: {f.size_2xl}px;
    font-weight: {f.weight_semibold};
}}
QLabel[role="sectionTitle"] {{
    font-size: {f.size_xl}px;
    font-weight: {f.weight_semibold};
}}
QLabel[role="cardTitle"] {{
    font-size: {f.size_lg}px;
    font-weight: {f.weight_semibold};
}}
QLabel[role="subheading"] {{
    font-size: {f.size_lg}px;
    font-weight: {f.weight_normal};
    color: {c.text_secondary};
}}
QLabel[role="body"] {{
    font-size: {f.size_md}px;
    color: {c.text_secondary};
}}
QLabel[role="caption"] {{
    font-size: {f.size_sm}px;
    color: {c.text_muted};
}}
QLabel[role="eyebrow"] {{
    font-size: {f.size_xs}px;
    font-weight: {f.weight_semibold};
    color: {c.text_tertiary};
}}
QLabel[role="stat"] {{
    font-family: {f.family_display};
    font-size: {f.size_2xl}px;
    font-weight: {f.weight_semibold};
    color: {c.text_primary};
}}
QLabel[role="mono"] {{
    font-family: {f.family_mono};
    font-size: {f.size_sm}px;
    color: {c.text_secondary};
}}
QLabel[tone="primary"]   {{ color: {c.primary}; }}
QLabel[tone="secondary"] {{ color: {c.secondary}; }}
QLabel[tone="success"]   {{ color: {c.success}; }}
QLabel[tone="warning"]   {{ color: {c.warning}; }}
QLabel[tone="error"]     {{ color: {c.error}; }}
QLabel[tone="muted"]     {{ color: {c.text_muted}; }}

/* ── Badges ──────────────────────────────────────────────────── */
QLabel[badge] {{
    font-size: {f.size_xs}px;
    font-weight: {f.weight_semibold};
    border-radius: {RADIUS.xs}px;
    padding: 3px 8px;
}}
QLabel[badge="neutral"] {{ background-color: {c.bg_tertiary};      color: {c.text_secondary}; }}
QLabel[badge="primary"] {{ background-color: {c.primary_subtle};   color: {c.primary}; }}
QLabel[badge="success"] {{ background-color: {c.success_subtle};   color: {c.success}; }}
QLabel[badge="warning"] {{ background-color: {c.warning_subtle};   color: {c.warning}; }}
QLabel[badge="error"]   {{ background-color: {c.error_subtle};     color: {c.error}; }}
QLabel[badge="info"]    {{ background-color: {c.info_subtle};      color: {c.info}; }}
QLabel[badge="secondary"] {{ background-color: {c.secondary_subtle}; color: {c.secondary}; }}

/* ── Buttons ─────────────────────────────────────────────────── */
QPushButton {{
    background-color: {c.bg_secondary};
    color: {c.text_primary};
    border: 1px solid {c.border_default};
    border-radius: {RADIUS.sm}px;
    padding: 7px 16px;
    font-size: {f.size_md}px;
    font-weight: {f.weight_medium};
    min-height: 18px;
}}
QPushButton:hover {{
    background-color: {c.bg_hover};
    border-color: {c.border_strong};
}}
QPushButton:pressed {{
    background-color: {c.bg_active};
}}
QPushButton:focus {{
    border-color: {c.primary};
}}
QPushButton:disabled {{
    color: {c.text_tertiary};
    background-color: {c.bg_tertiary};
    border-color: {c.border_subtle};
}}

QPushButton[role="primary"] {{
    background-color: {c.primary};
    color: {c.text_inverse};
    border: 1px solid {c.primary};
    font-weight: {f.weight_semibold};
    padding: 8px 20px;
}}
QPushButton[role="primary"]:hover {{
    background-color: {c.primary_hover};
    border-color: {c.primary_hover};
}}
QPushButton[role="primary"]:pressed {{
    background-color: {c.primary_pressed};
    border-color: {c.primary_pressed};
}}
QPushButton[role="primary"]:focus {{
    border-color: {c.primary_pressed};
}}
QPushButton[role="primary"]:disabled {{
    background-color: {c.bg_tertiary};
    color: {c.text_tertiary};
    border-color: {c.border_subtle};
}}

QPushButton[role="secondary"] {{
    background-color: {c.primary_subtle};
    color: {c.primary};
    border: 1px solid {c.primary_border};
    font-weight: {f.weight_semibold};
}}
QPushButton[role="secondary"]:hover {{
    background-color: {c.primary_subtle};
    border-color: {c.primary};
}}

QPushButton[role="ghost"] {{
    background: transparent;
    border: 1px solid transparent;
    color: {c.text_secondary};
    padding: 7px 12px;
    font-weight: {f.weight_medium};
}}
QPushButton[role="ghost"]:hover {{
    background-color: {c.bg_hover};
    color: {c.text_primary};
}}
QPushButton[role="ghost"]:pressed {{
    background-color: {c.bg_active};
}}
QPushButton[role="ghost"]:focus {{
    border-color: {c.primary_border};
}}
QPushButton[role="ghost"]:disabled {{
    background: transparent;
    color: {c.text_tertiary};
    border-color: transparent;
}}

QPushButton[role="danger"] {{
    background-color: {c.error_subtle};
    color: {c.error};
    border: 1px solid transparent;
    font-weight: {f.weight_semibold};
}}
QPushButton[role="danger"]:hover {{
    border-color: {c.error};
}}

QPushButton[role="link"] {{
    background: transparent;
    border: none;
    color: {c.primary};
    padding: 2px 4px;
    font-weight: {f.weight_semibold};
    text-align: left;
}}
QPushButton[role="link"]:hover {{
    color: {c.primary_hover};
}}

QPushButton[role="iconOnly"] {{
    background: transparent;
    border: 1px solid transparent;
    border-radius: {RADIUS.xs}px;
    padding: 0;
}}
QPushButton[role="iconOnly"]:hover {{
    background-color: {c.bg_hover};
}}
QPushButton[role="iconOnly"]:pressed {{
    background-color: {c.bg_active};
}}
QPushButton[role="iconOnly"]:focus {{
    border-color: {c.primary_border};
}}

QPushButton[role="chip"] {{
    background-color: {c.bg_secondary};
    color: {c.text_secondary};
    border: 1px solid {c.border_default};
    border-radius: {RADIUS.pill}px;
    padding: 5px 14px;
    font-size: {f.size_sm}px;
    font-weight: {f.weight_medium};
}}
QPushButton[role="chip"]:hover {{
    border-color: {c.primary_border};
    color: {c.text_primary};
}}
QPushButton[role="chip"][active="true"] {{
    background-color: {c.primary_subtle};
    border-color: {c.primary};
    color: {c.primary};
    font-weight: {f.weight_semibold};
}}

/* ── Inputs ──────────────────────────────────────────────────── */
QLineEdit {{
    background-color: {c.bg_secondary};
    color: {c.text_primary};
    border: 1px solid {c.border_default};
    border-radius: {RADIUS.sm}px;
    padding: 7px 12px;
    font-size: {f.size_md}px;
    selection-background-color: {c.primary};
    selection-color: {c.text_inverse};
}}
QLineEdit:hover {{
    border-color: {c.border_strong};
}}
QLineEdit:focus {{
    border-color: {c.primary};
}}
QLineEdit:disabled {{
    background-color: {c.bg_tertiary};
    color: {c.text_tertiary};
}}
QLineEdit[invalid="true"] {{
    border-color: {c.error};
    background-color: {c.error_subtle};
}}

QComboBox {{
    background-color: {c.bg_secondary};
    color: {c.text_primary};
    border: 1px solid {c.border_default};
    border-radius: {RADIUS.sm}px;
    padding: 6px 10px;
    font-size: {f.size_sm}px;
    min-height: 20px;
}}
QComboBox:hover {{
    border-color: {c.border_strong};
}}
QComboBox:focus {{
    border-color: {c.primary};
}}
QComboBox::drop-down {{
    border: none;
    width: 24px;
    subcontrol-origin: padding;
    subcontrol-position: center right;
}}
QComboBox::down-arrow {{
    image: url("{chevron}");
    width: 12px;
    height: 12px;
}}
QComboBox QAbstractItemView {{
    background-color: {c.bg_elevated};
    color: {c.text_primary};
    border: 1px solid {c.border_default};
    border-radius: {RADIUS.sm}px;
    padding: 4px;
    outline: none;
    selection-background-color: {c.primary_subtle};
    selection-color: {c.primary};
}}
QComboBox QAbstractItemView::item {{
    padding: 6px 10px;
    border-radius: {RADIUS.xs}px;
    min-height: 22px;
}}

QSpinBox {{
    background-color: {c.bg_secondary};
    color: {c.text_primary};
    border: 1px solid {c.border_default};
    border-radius: {RADIUS.sm}px;
    padding: 5px 8px;
    font-size: {f.size_sm}px;
    min-height: 20px;
}}
QSpinBox:hover {{ border-color: {c.border_strong}; }}
QSpinBox:focus {{ border-color: {c.primary}; }}
QSpinBox::up-button, QSpinBox::down-button {{
    background: transparent;
    border: none;
    width: 16px;
}}
QSpinBox::up-arrow {{
    image: url("{up}");
    width: 9px; height: 9px;
}}
QSpinBox::down-arrow {{
    image: url("{up}");
    width: 9px; height: 9px;
}}

QTextEdit, QPlainTextEdit {{
    background-color: {c.bg_tertiary};
    color: {c.text_primary};
    border: 1px solid {c.border_subtle};
    border-radius: {RADIUS.md}px;
    padding: 10px;
    font-family: {f.family_mono};
    font-size: {f.size_sm}px;
    selection-background-color: {c.primary};
    selection-color: {c.text_inverse};
}}

/* ── Check / radio ───────────────────────────────────────────── */
QCheckBox {{
    color: {c.text_primary};
    spacing: 8px;
    font-size: {f.size_sm}px;
    padding: 2px 0;
}}
QCheckBox:disabled {{ color: {c.text_tertiary}; }}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border-radius: 5px;
    border: 1.5px solid {c.border_strong};
    background-color: {c.bg_secondary};
}}
QCheckBox::indicator:hover {{
    border-color: {c.primary};
}}
QCheckBox::indicator:checked {{
    background-color: {c.primary};
    border-color: {c.primary};
    image: url("{check}");
}}
QCheckBox::indicator:indeterminate {{
    background-color: {c.primary_subtle};
    border-color: {c.primary};
}}

QRadioButton {{
    color: {c.text_primary};
    spacing: 8px;
    font-size: {f.size_sm}px;
    padding: 2px 0;
}}
QRadioButton:disabled {{ color: {c.text_tertiary}; }}
QRadioButton::indicator {{
    width: 15px;
    height: 15px;
    border-radius: 8px;
    border: 1.5px solid {c.border_strong};
    background-color: {c.bg_secondary};
}}
QRadioButton::indicator:hover {{ border-color: {c.primary}; }}
QRadioButton::indicator:checked {{
    border: 5px solid {c.primary};
    background-color: {c.bg_secondary};
}}

/* ── Tables ──────────────────────────────────────────────────── */
QTableView, QTableWidget {{
    background-color: {c.bg_secondary};
    alternate-background-color: {c.table_row_alt};
    color: {c.text_primary};
    border: 1px solid {c.border_subtle};
    border-radius: {RADIUS.md}px;
    gridline-color: {c.table_grid};
    selection-background-color: {c.table_selection};
    selection-color: {c.text_primary};
    font-size: {f.size_sm}px;
}}
QTableView::item, QTableWidget::item {{
    padding: 6px 8px;
    border: none;
}}
QTableView::item:selected, QTableWidget::item:selected {{
    background-color: {c.table_selection};
    color: {c.text_primary};
}}
QHeaderView {{
    background-color: {c.table_header_bg};
    border: none;
}}
QHeaderView::section {{
    background-color: {c.table_header_bg};
    color: {c.text_secondary};
    font-size: {f.size_xs}px;
    font-weight: {f.weight_semibold};
    padding: 8px 10px;
    border: none;
    border-bottom: 1px solid {c.border_subtle};
    border-right: 1px solid {c.border_subtle};
}}
QHeaderView::section:vertical {{
    color: {c.text_tertiary};
    padding: 4px 8px;
}}
QTableCornerButton::section {{
    background-color: {c.table_header_bg};
    border: none;
    border-bottom: 1px solid {c.border_subtle};
    border-right: 1px solid {c.border_subtle};
}}

/* ── Progress ────────────────────────────────────────────────── */
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
    background-color: {c.primary};
    border-radius: 4px;
}}
QProgressBar[role="thick"] {{
    min-height: 10px;
    max-height: 10px;
    border-radius: 5px;
}}
QProgressBar[role="thick"]::chunk {{
    border-radius: 5px;
}}

/* ── Lists ───────────────────────────────────────────────────── */
QListWidget {{
    background-color: transparent;
    border: none;
    color: {c.text_primary};
    font-size: {f.size_md}px;
    outline: none;
}}
QListWidget::item {{
    padding: 9px 12px;
    border-radius: {RADIUS.sm}px;
    border: none;
    color: {c.text_primary};
}}
QListWidget::item:hover {{
    background-color: {c.bg_hover};
}}
QListWidget::item:selected {{
    background-color: {c.primary_subtle};
    color: {c.primary};
}}

/* ── Scrollbars ──────────────────────────────────────────────── */
QScrollArea {{
    background: transparent;
    border: none;
}}
QScrollArea > QWidget > QWidget {{
    background: transparent;
}}
QScrollBar:vertical {{
    background: {c.scrollbar_bg};
    width: 10px;
    margin: 2px;
    border: none;
    border-radius: 5px;
}}
QScrollBar::handle:vertical {{
    background: {c.scrollbar_handle};
    min-height: 32px;
    border-radius: 3px;
}}
QScrollBar::handle:vertical:hover {{
    background: {c.scrollbar_handle_hover};
}}
QScrollBar:horizontal {{
    background: {c.scrollbar_bg};
    height: 10px;
    margin: 2px;
    border: none;
    border-radius: 5px;
}}
QScrollBar::handle:horizontal {{
    background: {c.scrollbar_handle};
    min-width: 32px;
    border-radius: 3px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {c.scrollbar_handle_hover};
}}
QScrollBar::add-line, QScrollBar::sub-line,
QScrollBar::add-page, QScrollBar::sub-page {{
    background: none;
    border: none;
    width: 0px;
    height: 0px;
}}

/* ── Drop zone ───────────────────────────────────────────────── */
QFrame#dropZone {{
    background-color: {c.drop_zone_bg};
    border: 2px dashed {c.drop_zone_border};
    border-radius: {RADIUS.xl}px;
}}
QFrame#dropZone:hover {{
    border-color: {c.primary};
    background-color: {c.drop_zone_active_bg};
}}
QFrame#dropZone[dragActive="true"] {{
    border-color: {c.drop_zone_active_border};
    background-color: {c.drop_zone_active_bg};
}}

/* ── Banners ─────────────────────────────────────────────────── */
QFrame[banner] {{
    border-radius: {RADIUS.md}px;
    border: 1px solid transparent;
}}
QFrame[banner="success"] {{ background-color: {c.success_subtle}; border-color: {c.success}; }}
QFrame[banner="warning"] {{ background-color: {c.warning_subtle}; border-color: {c.warning}; }}
QFrame[banner="error"]   {{ background-color: {c.error_subtle};   border-color: {c.error}; }}
QFrame[banner="info"]    {{ background-color: {c.info_subtle};    border-color: {c.info}; }}
QFrame[banner="success"] QLabel {{ color: {c.success}; }}
QFrame[banner="warning"] QLabel {{ color: {c.warning}; }}
QFrame[banner="error"]   QLabel {{ color: {c.error}; }}
QFrame[banner="info"]    QLabel {{ color: {c.info}; }}

/* ── Dialogs & modals ────────────────────────────────────────── */
QDialog {{
    background-color: {c.bg_elevated};
    color: {c.text_primary};
}}
QFrame#modalHeader {{
    background-color: {c.bg_elevated};
    border: none;
    border-bottom: 1px solid {c.border_subtle};
}}
QFrame#modalBody {{
    background-color: {c.bg_primary};
    border: none;
}}
QFrame#modalFooter {{
    background-color: {c.bg_elevated};
    border: none;
    border-top: 1px solid {c.border_subtle};
}}
QLabel#modalTitle {{
    font-family: {f.family_display};
    font-size: {f.size_xl}px;
    font-weight: {f.weight_semibold};
    color: {c.text_primary};
}}
QLabel#modalSubtitle {{
    font-size: {f.size_sm}px;
    color: {c.text_secondary};
}}

/* ── Toast ───────────────────────────────────────────────────── */
QFrame#toast {{
    background-color: {c.bg_elevated};
    border: 1px solid {c.border_default};
    border-radius: {RADIUS.md}px;
}}
QFrame#toast QLabel {{
    color: {c.text_primary};
    font-size: {f.size_md}px;
    font-weight: {f.weight_medium};
}}

/* ── Tabs ────────────────────────────────────────────────────── */
QTabWidget {{
    background: transparent;
}}
QTabWidget::pane {{
    border: 1px solid {c.border_subtle};
    border-radius: {RADIUS.md}px;
    background-color: {c.bg_secondary};
    top: -1px;
}}
QTabWidget::tab-bar {{
    left: 2px;
}}
QTabBar {{
    background: transparent;
    border: none;
}}
QTabBar::tab {{
    background: transparent;
    color: {c.text_secondary};
    border: none;
    padding: 8px 16px;
    margin-right: 4px;
    border-radius: {RADIUS.sm}px;
    font-size: {f.size_sm}px;
    font-weight: {f.weight_medium};
}}
QTabBar::tab:hover {{
    background-color: {c.bg_hover};
    color: {c.text_primary};
}}
QTabBar::tab:selected {{
    background-color: {c.primary_subtle};
    color: {c.primary};
    font-weight: {f.weight_semibold};
}}

/* ── Group box ───────────────────────────────────────────────── */
QGroupBox {{
    border: 1px solid {c.border_subtle};
    border-radius: {RADIUS.md}px;
    margin-top: 14px;
    padding-top: 12px;
    font-weight: {f.weight_semibold};
    background-color: {c.bg_secondary};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 6px;
    color: {c.text_secondary};
}}

/* ── Menus ───────────────────────────────────────────────────── */
QMenu {{
    background-color: {c.bg_elevated};
    color: {c.text_primary};
    border: 1px solid {c.border_default};
    border-radius: {RADIUS.sm}px;
    padding: 6px 4px;
}}
QMenu::item {{
    padding: 8px 24px 8px 12px;
    border-radius: {RADIUS.xs}px;
    margin: 1px 4px;
}}
QMenu::item:selected {{
    background-color: {c.primary_subtle};
    color: {c.primary};
}}
QMenu::separator {{
    height: 1px;
    background: {c.border_subtle};
    margin: 4px 8px;
}}

/* ── Tooltips ────────────────────────────────────────────────── */
QToolTip {{
    background-color: {c.bg_elevated};
    color: {c.text_primary};
    border: 1px solid {c.border_default};
    border-radius: {RADIUS.xs}px;
    padding: 6px 10px;
    font-size: {f.size_sm}px;
}}

/* ── Step indicator ──────────────────────────────────────────── */
QLabel[step="done"] {{
    background-color: {c.success_subtle};
    color: {c.success};
    border-radius: {RADIUS.pill}px;
    padding: 4px 12px;
    font-size: {f.size_xs}px;
    font-weight: {f.weight_semibold};
}}
QLabel[step="current"] {{
    background-color: {c.primary};
    color: {c.text_inverse};
    border-radius: {RADIUS.pill}px;
    padding: 4px 12px;
    font-size: {f.size_xs}px;
    font-weight: {f.weight_semibold};
}}
QLabel[step="todo"] {{
    background-color: {c.bg_tertiary};
    color: {c.text_tertiary};
    border-radius: {RADIUS.pill}px;
    padding: 4px 12px;
    font-size: {f.size_xs}px;
    font-weight: {f.weight_medium};
}}

/* ── Splitter ────────────────────────────────────────────────── */
QSplitter::handle {{
    background-color: transparent;
}}
QSplitter::handle:horizontal {{ width: {SIZE.icon_sm}px; }}
QSplitter::handle:vertical {{ height: {SIZE.icon_sm}px; }}
QSplitter::handle:hover {{
    background-color: {c.primary_subtle};
}}
"""
