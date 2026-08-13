"""Compact summary card for a configured transformation step.

Shows, in plain language, what the step will do:
* friendly title and category
* the columns it touches
* a short summary of its settings
* Configure / Remove actions

The card is presentation only — it holds a reference to the
:class:`TransformStep` it describes and never mutates it.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QWidget

from deskx.gui.theme import ColorPalette, SIZE, SPACE, palette
from deskx.gui.theme.icons import Icon, get_pixmap, icon_label
from deskx.gui.widgets.components import Badge, IconButton, Themed, label
from deskx.processing.pipeline import TransformStep
from deskx.processing.transform_catalog import get_transform_metadata

# Category → icon, so the pipeline reads at a glance.
CATEGORY_ICONS: dict[str, str] = {
    "Cleaning": Icon.CLEAN,
    "Columns": Icon.COLUMNS,
    "Missing Values": Icon.TABLE,
    "Type Normalization": Icon.TYPE,
    "Filtering": Icon.FILTER,
    "Privacy": Icon.SHIELD,
    "Statistical Privacy": Icon.GENERALIZE,
}

# A few transforms deserve their own glyph rather than the category's.
_TRANSFORM_ICON_OVERRIDES: dict[str, str] = {
    "Mask Email & Text": Icon.MASK,
    "Redact Confidential Data": Icon.REDACT,
    "Hash Identifiers": Icon.HASH,
    "Pseudonymize (Fake IDs)": Icon.PSEUDONYM,
    "Normalize Date Formats": Icon.CALENDAR,
}

# Parameter keys rendered with friendlier wording in the settings line.
_PARAM_LABELS: dict[str, str] = {
    "show_last": "keeping last",
    "replacement": "replaced with",
    "prefix": "prefix",
    "round_to": "rounded to",
    "threshold": "minimum group size",
    "strategy": "strategy",
    "value": "value",
    "keep": "keep",
    "find": "find",
    "replace": "replace with",
    "operator": "condition",
}


def icon_for(metadata) -> str:
    """Return the icon name that best represents a transformation."""
    override = _TRANSFORM_ICON_OVERRIDES.get(metadata.friendly_name)
    if override:
        return override
    return CATEGORY_ICONS.get(metadata.category, Icon.TRANSFORM)


class TransformSummaryCard(QFrame, Themed):
    """Card describing one active step in the pipeline."""

    edit_requested = Signal(object)  # Emits self.step
    remove_requested = Signal(object)  # Emits self.step

    def __init__(self, step: TransformStep, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.step = step
        self.metadata = get_transform_metadata(step.transform_type)
        self._icon_name = icon_for(self.metadata)
        self.setProperty("role", "card")
        self._setup_ui()
        self._register_theme()

    # ── UI ──────────────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(SPACE.md, SPACE.md, SPACE.md, SPACE.md)
        root.setSpacing(SPACE.md)

        self._icon_lbl = icon_label(self._icon_name, palette().primary, SIZE.icon_lg)
        root.addWidget(self._icon_lbl, 0, Qt.AlignmentFlag.AlignTop)

        text_col = QVBoxLayout()
        text_col.setContentsMargins(0, 0, 0, 0)
        text_col.setSpacing(SPACE.xs)

        title_row = QHBoxLayout()
        title_row.setContentsMargins(0, 0, 0, 0)
        title_row.setSpacing(SPACE.sm)
        title_row.addWidget(label(self.metadata.friendly_name, "cardTitle"))
        title_row.addWidget(Badge(self.metadata.category, "primary"))
        title_row.addStretch()
        text_col.addLayout(title_row)

        text_col.addWidget(label(self.metadata.one_liner, "caption", wrap=True))

        summary = self._summary_line()
        summary_lbl = label(summary, "body", wrap=True)
        summary_lbl.setToolTip(summary)
        text_col.addWidget(summary_lbl)

        root.addLayout(text_col, 1)

        actions = QVBoxLayout()
        actions.setContentsMargins(0, 0, 0, 0)
        actions.setSpacing(SPACE.xs)

        configure = IconButton(Icon.EDIT, "Configure this transformation", 28)
        configure.clicked.connect(lambda: self.edit_requested.emit(self.step))
        actions.addWidget(configure)

        remove = IconButton(Icon.TRASH, "Remove from pipeline", 28)
        remove.clicked.connect(lambda: self.remove_requested.emit(self.step))
        actions.addWidget(remove)

        actions.addStretch()
        root.addLayout(actions)

    def _summary_line(self) -> str:
        columns = self._format_columns()
        settings = self._format_params()
        line = f"Applies to  {columns}"
        if settings:
            line += f"   ·   {settings}"
        return line

    # ── Formatting (kept stable — covered by unit tests) ────────────

    def _format_columns(self) -> str:
        p = self.step.params
        if "column" in p and p["column"]:
            return str(p["column"])
        if "columns" in p and p["columns"]:
            return ", ".join(p["columns"])
        if "subset" in p and p["subset"]:
            return ", ".join(p["subset"])
        return "All Columns"

    def _format_params(self) -> str:
        p = self.step.params
        parts = []
        for k, v in p.items():
            if k in {"column", "columns", "subset"}:
                continue
            parts.append(f"{k}: {v}")
        return ", ".join(parts)

    def friendly_params(self) -> str:
        """Human-readable settings summary used in the review pipeline."""
        parts = []
        for key, value in self.step.params.items():
            if key in {"column", "columns", "subset"} or value in ("", None):
                continue
            parts.append(f"{_PARAM_LABELS.get(key, key)} {value}")
        return ", ".join(parts)

    def apply_theme(self, p: ColorPalette) -> None:
        self._icon_lbl.setPixmap(get_pixmap(self._icon_name, p.primary, SIZE.icon_lg))
