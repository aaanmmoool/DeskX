"""Transformation workspace.

Three stacked sections, each a card:

1. **Sensitive data** — columns the detector flagged, each with a
   one-click protection choice.
2. **Add a transformation** — the full catalog, filtered by category,
   with a plain-English description on every entry.
3. **Your pipeline** — the steps that will run, in order.

The class name is kept as ``TransformSidebar`` because it is part of
the existing public surface; it is no longer a narrow rail.
"""

from __future__ import annotations

from typing import Any

import pandas as pd
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
)

from deskx.gui.theme import ColorPalette, SIZE, SPACE, palette
from deskx.gui.theme.icons import Icon, get_pixmap, icon_label
from deskx.gui.widgets.components import (
    Badge,
    Button,
    Card,
    ChipButton,
    ClickableCard,
    EmptyState,
    SectionHeader,
    Themed,
    clear_layout,
    label,
)
from deskx.gui.widgets.transform_config_dialog import TransformConfigDialog
from deskx.gui.widgets.transform_summary_card import (
    TransformSummaryCard,
    icon_for,
)
from deskx.processing.pipeline import (
    TRANSFORM_INFO,
    TransformStep,
    TransformType,
)
from deskx.processing.sensitive_detector import SensitiveColumn
from deskx.processing.transform_catalog import get_transform_metadata

# ── Privacy quick actions ──────────────────────────────────────────
_PRIVACY_ACTIONS = {
    "mask": TransformType.MASK_COLUMN,
    "redact": TransformType.REDACT_COLUMN,
    "hash": TransformType.HASH_COLUMN,
    "pseudonymize": TransformType.PSEUDONYMIZE_COLUMN,
    "generalize": TransformType.GENERALIZE_COLUMN,
    "ignore": None,
}

_PRIVACY_TRANSFORMS = frozenset({
    TransformType.MASK_COLUMN,
    TransformType.REDACT_COLUMN,
    TransformType.HASH_COLUMN,
    TransformType.PSEUDONYMIZE_COLUMN,
})

_SENSITIVE_ACTIONS = ["Ignore", "Mask", "Redact", "Hash", "Pseudonymize"]

_ALL_CATEGORIES = "All"

_CATALOG_COLUMNS = 2


class TransformSidebar(QWidget, Themed):
    """Builds a transformation pipeline.

    Signals
    -------
    pipeline_changed(list)
        Emitted with the list of ``TransformStep`` whenever the
        pipeline changes.
    """

    pipeline_changed = Signal(list)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._columns: list[str] = []
        self._sample_df: pd.DataFrame | None = None
        self._summary_cards: list[TransformSummaryCard] = []
        self._active_category: str = _ALL_CATEGORIES
        self._catalog_cards: list[tuple[QWidget, str]] = []
        # Retained for backwards compatibility with older callers.
        self._step_widgets: list[Any] = []
        self._setup_ui()
        self._register_theme()

    # ── Public API ──────────────────────────────────────────────────

    def set_columns(self, columns: list[str]) -> None:
        """Update the columns offered when configuring a transformation."""
        self._columns = columns

    def set_sample_data(self, df: pd.DataFrame | None) -> None:
        """Provide sample rows so config modals can show a live preview."""
        self._sample_df = df

    def set_sensitive_columns(self, sensitive: list[SensitiveColumn]) -> None:
        """Show a protection control for each column the detector flagged."""
        clear_layout(self._sensitive_layout)

        if not sensitive:
            self._sensitive_card.setVisible(False)
            return

        self._sensitive_card.setVisible(True)
        self._sensitive_count.setText(
            f"{len(sensitive)} column{'s' if len(sensitive) != 1 else ''}"
        )

        for detected in sensitive[:6]:
            self._sensitive_layout.addWidget(self._make_sensitive_row(detected))

    def get_pipeline(self) -> list[TransformStep]:
        """Return the current pipeline as a list of ``TransformStep``."""
        return [card.step for card in self._summary_cards]

    def add_step(self, step: TransformStep) -> None:
        """Programmatically append a transformation step."""
        self._add_card(step)
        self._emit_pipeline()

    def clear_pipeline(self) -> None:
        """Remove every configured transformation."""
        for card in list(self._summary_cards):
            self._remove_card(card)
        self._emit_pipeline()

    def pipeline_cards(self) -> list[TransformSummaryCard]:
        """Return the summary cards, in pipeline order."""
        return list(self._summary_cards)

    # ── Setup ───────────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(SPACE.lg)

        root.addWidget(self._build_sensitive_card())
        root.addWidget(self._build_catalog_card())
        root.addWidget(self._build_pipeline_card())
        root.addStretch()

    def _build_sensitive_card(self) -> QWidget:
        self._sensitive_card = Card(padding=SPACE.xl, spacing=SPACE.md)

        header = SectionHeader(
            "Sensitive data detected",
            Icon.WARNING,
            "DeskX scanned your columns for personal information. "
            "Choose how each one should be protected.",
        )
        self._sensitive_count = Badge("", "warning")
        header.add_trailing(self._sensitive_count)
        self._sensitive_card.add(header)

        self._sensitive_layout = QVBoxLayout()
        self._sensitive_layout.setSpacing(SPACE.sm)
        self._sensitive_card.add_layout(self._sensitive_layout)

        self._sensitive_card.setVisible(False)
        return self._sensitive_card

    def _make_sensitive_row(self, detected: SensitiveColumn) -> QWidget:
        row = QFrame()
        row.setProperty("role", "cardFlat")
        layout = QHBoxLayout(row)
        layout.setContentsMargins(SPACE.md, SPACE.sm, SPACE.md, SPACE.sm)
        layout.setSpacing(SPACE.md)

        layout.addWidget(icon_label(Icon.SHIELD, palette().warning, SIZE.icon_md))

        text_col = QVBoxLayout()
        text_col.setContentsMargins(0, 0, 0, 0)
        text_col.setSpacing(0)
        name = label(detected.column_name, "body")
        name.setToolTip(detected.reason)
        text_col.addWidget(name)
        text_col.addWidget(
            label(
                f"Looks like {detected.category.replace('_', ' ')} "
                f"· {detected.confidence:.0%} confidence",
                "caption",
            )
        )
        layout.addLayout(text_col, 1)

        action_combo = QComboBox()
        action_combo.setFixedWidth(150)
        action_combo.addItems(_SENSITIVE_ACTIONS)
        action_combo.setToolTip(
            "Mask keeps part of the value visible.  Redact removes it entirely.  "
            "Hash creates an irreversible fingerprint.  Pseudonymize swaps in a "
            "consistent fake label."
        )

        # Connect before selecting so the detector's suggestion is
        # applied to the pipeline automatically.
        action_combo.currentTextChanged.connect(
            lambda action, col=detected.column_name: self._on_sensitive_action(
                col, action
            )
        )

        suggested = detected.suggested_action.capitalize()
        action_combo.setCurrentText(
            suggested if suggested in _SENSITIVE_ACTIONS else "Ignore"
        )

        layout.addWidget(action_combo)
        return row

    def _build_catalog_card(self) -> QWidget:
        card = Card(padding=SPACE.xl, spacing=SPACE.md)
        card.add(
            SectionHeader(
                "Add a transformation",
                Icon.PLUS,
                "Pick a rule to apply. You can configure it before it is added.",
            )
        )

        categories = [_ALL_CATEGORIES]
        for info in TRANSFORM_INFO.values():
            category = info.get("category", "Other")
            if category not in categories:
                categories.append(category)

        chips = QHBoxLayout()
        chips.setSpacing(SPACE.xs + 2)
        self._category_chips: list[ChipButton] = []
        for category in categories:
            chip = ChipButton(category)
            chip.setChecked(category == _ALL_CATEGORIES)
            chip.clicked.connect(
                lambda _=False, name=category: self._set_category(name)
            )
            chips.addWidget(chip)
            self._category_chips.append(chip)
        chips.addStretch()
        card.add_layout(chips)

        grid_host = QWidget()
        self._catalog_grid = QGridLayout(grid_host)
        self._catalog_grid.setContentsMargins(0, 0, 0, 0)
        self._catalog_grid.setHorizontalSpacing(SPACE.sm)
        self._catalog_grid.setVerticalSpacing(SPACE.sm)
        card.add(grid_host)

        self._populate_catalog()
        return card

    def _populate_catalog(self) -> None:
        for transform_type in TRANSFORM_INFO:
            metadata = get_transform_metadata(transform_type)
            self._catalog_cards.append(
                (self._make_catalog_card(transform_type, metadata), metadata.category)
            )
        self._relayout_catalog()

    def _make_catalog_card(self, transform_type: TransformType, metadata) -> QWidget:
        card = ClickableCard(padding=SPACE.md, spacing=SPACE.xs, variant="cardFlat")
        card.setToolTip(metadata.what_it_does)

        head = QHBoxLayout()
        head.setContentsMargins(0, 0, 0, 0)
        head.setSpacing(SPACE.sm)
        glyph = icon_label(icon_for(metadata), palette().primary, SIZE.icon_md)
        head.addWidget(glyph, 0, Qt.AlignmentFlag.AlignTop)
        head.addWidget(label(metadata.friendly_name, "body"), 1)
        card.add_layout(head)

        card.add(label(metadata.one_liner, "caption", wrap=True))
        card.clicked.connect(
            lambda tt=transform_type: self._open_modal_for_transform(tt)
        )
        self._catalog_glyphs = getattr(self, "_catalog_glyphs", [])
        self._catalog_glyphs.append((glyph, icon_for(metadata)))
        return card

    def _relayout_catalog(self) -> None:
        while self._catalog_grid.count():
            self._catalog_grid.takeAt(0)

        visible = [
            widget
            for widget, category in self._catalog_cards
            if self._active_category in (_ALL_CATEGORIES, category)
        ]
        for widget, category in self._catalog_cards:
            widget.setVisible(
                self._active_category in (_ALL_CATEGORIES, category)
            )

        for index, widget in enumerate(visible):
            self._catalog_grid.addWidget(
                widget, index // _CATALOG_COLUMNS, index % _CATALOG_COLUMNS
            )

    def _set_category(self, category: str) -> None:
        self._active_category = category
        for chip in self._category_chips:
            match = chip.text() == category
            if chip.isChecked() != match:
                chip.setChecked(match)
        self._relayout_catalog()

    def _build_pipeline_card(self) -> QWidget:
        card = Card(padding=SPACE.xl, spacing=SPACE.md)

        header = SectionHeader(
            "Your pipeline",
            Icon.PIPELINE,
            "Steps run top to bottom on a copy of your data.",
        )
        self._pipeline_badge = Badge("0 steps", "neutral")
        header.add_trailing(self._pipeline_badge)

        clear_btn = Button("Clear all", icon=Icon.TRASH, role="ghost")
        clear_btn.setToolTip("Remove every transformation from the pipeline")
        clear_btn.clicked.connect(self.clear_pipeline)
        header.add_trailing(clear_btn)
        card.add(header)

        self._steps_layout = QVBoxLayout()
        self._steps_layout.setSpacing(SPACE.sm)
        card.add_layout(self._steps_layout)

        self._pipeline_empty = EmptyState(
            Icon.PIPELINE,
            "No transformations yet",
            "Your file will be copied as-is. Add a rule above to clean or "
            "protect the data.",
        )
        card.add(self._pipeline_empty)
        return card

    # ── Slots ───────────────────────────────────────────────────────

    def _open_modal_for_transform(
        self,
        transform_type: TransformType,
        existing_step: TransformStep | None = None,
    ) -> None:
        dialog = TransformConfigDialog(
            transform_type=transform_type,
            available_columns=self._columns,
            sample_df=self._sample_df,
            existing_step=existing_step,
            parent=self,
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            if existing_step:
                card_to_remove = next(
                    (c for c in self._summary_cards if c.step == existing_step),
                    None,
                )
                if card_to_remove:
                    self._remove_card(card_to_remove)
            for step in dialog.get_steps():
                self._add_card(step)
            self._emit_pipeline()

    def _on_sensitive_action(self, column: str, action: str) -> None:
        action_lower = action.lower()
        if action_lower == "ignore":
            for card in list(self._summary_cards):
                if (
                    card.step.params.get("column") == column
                    and card.step.transform_type in _PRIVACY_TRANSFORMS
                ):
                    self._remove_card(card)
            self._emit_pipeline()
            return

        transform_type = _PRIVACY_ACTIONS.get(action_lower)
        if transform_type is None:
            return

        for card in self._summary_cards:
            if (
                card.step.transform_type == transform_type
                and card.step.params.get("column") == column
            ):
                return

        # Swap out any other protection already applied to this column.
        for card in list(self._summary_cards):
            if (
                card.step.params.get("column") == column
                and card.step.transform_type in _PRIVACY_TRANSFORMS
            ):
                self._remove_card(card)

        self._add_card(
            TransformStep(transform_type=transform_type, params={"column": column})
        )
        self._emit_pipeline()

    def _add_card(self, step: TransformStep) -> None:
        card = TransformSummaryCard(step)
        card.edit_requested.connect(self._on_edit_requested)
        card.remove_requested.connect(self._on_remove_requested)
        self._summary_cards.append(card)
        self._steps_layout.addWidget(card)

    def _remove_card(self, card: TransformSummaryCard) -> None:
        if card in self._summary_cards:
            self._summary_cards.remove(card)
            self._steps_layout.removeWidget(card)
            card.setParent(None)
            card.deleteLater()

    def _on_edit_requested(self, step: TransformStep) -> None:
        self._open_modal_for_transform(step.transform_type, existing_step=step)

    def _on_remove_requested(self, step: TransformStep) -> None:
        card = next((c for c in self._summary_cards if c.step == step), None)
        if card:
            self._remove_card(card)
            self._emit_pipeline()

    def _emit_pipeline(self) -> None:
        pipeline = self.get_pipeline()
        count = len(pipeline)
        self._pipeline_badge.set_content(
            f"{count} step{'s' if count != 1 else ''}",
            "primary" if count else "neutral",
        )
        self._pipeline_empty.setVisible(count == 0)
        self.pipeline_changed.emit(pipeline)

    def apply_theme(self, p: ColorPalette) -> None:
        for glyph, icon_name in getattr(self, "_catalog_glyphs", []):
            glyph.setPixmap(get_pixmap(icon_name, p.primary, SIZE.icon_md))
