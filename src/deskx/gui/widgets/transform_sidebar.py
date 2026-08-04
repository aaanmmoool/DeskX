"""Transformation pipeline builder sidebar.

Allows users to add, configure, reorder, and remove transformation
steps.  Emits the current pipeline configuration as a list of
:class:`TransformStep` objects.
"""

from __future__ import annotations

from typing import Any
import pandas as pd

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from deskx.processing.pipeline import (
    TRANSFORM_INFO,
    TransformStep,
    TransformType,
)
from deskx.processing.sensitive_detector import SensitiveColumn
from deskx.gui.widgets.transform_config_dialog import TransformConfigDialog
from deskx.gui.widgets.transform_summary_card import TransformSummaryCard



# ── Privacy quick actions ──────────────────────────────────────────
_PRIVACY_ACTIONS = {
    "mask": TransformType.MASK_COLUMN,
    "redact": TransformType.REDACT_COLUMN,
    "hash": TransformType.HASH_COLUMN,
    "pseudonymize": TransformType.PSEUDONYMIZE_COLUMN,
    "generalize": TransformType.GENERALIZE_COLUMN,
    "ignore": None,
}


class TransformStepWidget(QFrame):
    """A single transform step in the pipeline with remove button."""

    removed = Signal(object)  # Emits self

    def __init__(
        self,
        step: TransformStep,
        columns: list[str],
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.step = step
        self.setProperty("role", "card")
        self._columns = columns
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        # Header row: name + remove button
        header = QHBoxLayout()
        header.setSpacing(8)
        info = TRANSFORM_INFO.get(self.step.transform_type, {})
        name = info.get("name", self.step.transform_type.name)
        category = info.get("category", "")

        name_label = QLabel(f"  {name}")
        name_label.setStyleSheet("font-weight: 600;")
        header.addWidget(name_label)

        if category:
            cat_label = QLabel(category)
            cat_label.setProperty("role", "caption")
            header.addWidget(cat_label)

        header.addStretch()

        remove_btn = QPushButton("✕")
        remove_btn.setFixedSize(24, 24)
        remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        remove_btn.setProperty("role", "ghost")
        remove_btn.setToolTip("Remove this step")
        remove_btn.clicked.connect(lambda: self.removed.emit(self))
        header.addWidget(remove_btn)

        layout.addLayout(header)

        # Parameter widgets (based on transform type)
        self._add_param_widgets(layout)

    def _add_param_widgets(self, layout: QVBoxLayout) -> None:
        """Add parameter input widgets based on transform type."""
        tt = self.step.transform_type

        # Transforms that need a column selector
        col_transforms = {
            TransformType.FILL_MISSING,
            TransformType.NORMALIZE_DATES,
            TransformType.NORMALIZE_NUMBERS,
            TransformType.NORMALIZE_BOOLEANS,
            TransformType.FILTER_ROWS,
            TransformType.REPLACE_VALUES,
            TransformType.MASK_COLUMN,
            TransformType.REDACT_COLUMN,
            TransformType.HASH_COLUMN,
            TransformType.PSEUDONYMIZE_COLUMN,
            TransformType.GENERALIZE_COLUMN,
            TransformType.REVENUE_BANDS,
            TransformType.SUPPRESS_LOW_COUNTS,
        }

        if tt in col_transforms:
            row = QHBoxLayout()
            row.setSpacing(6)
            lbl = QLabel("Column:")
            lbl.setProperty("role", "caption")
            lbl.setFixedWidth(55)
            row.addWidget(lbl)
            col_combo = QComboBox()
            col_combo.addItems(self._columns)
            # Set from params if available
            current = self.step.params.get("column", "")
            if current in self._columns:
                col_combo.setCurrentText(current)
            elif self._columns:
                self.step.params["column"] = self._columns[0]
            col_combo.currentTextChanged.connect(
                lambda t: self.step.params.__setitem__("column", t)
            )
            row.addWidget(col_combo)
            layout.addLayout(row)

        # Strategy for fill_missing
        if tt == TransformType.FILL_MISSING:
            row = QHBoxLayout()
            row.setSpacing(6)
            lbl = QLabel("Strategy:")
            lbl.setProperty("role", "caption")
            lbl.setFixedWidth(55)
            row.addWidget(lbl)
            strat = QComboBox()
            strat.addItems([
                "value", "mean", "median", "mode",
                "forward", "backward", "drop",
            ])
            strat.setCurrentText(
                self.step.params.get("strategy", "value")
            )
            strat.currentTextChanged.connect(
                lambda t: self.step.params.__setitem__("strategy", t)
            )
            row.addWidget(strat)
            layout.addLayout(row)

        # Columns list for remove_columns
        if tt == TransformType.REMOVE_COLUMNS:
            row = QHBoxLayout()
            row.setSpacing(6)
            lbl = QLabel("Columns:")
            lbl.setProperty("role", "caption")
            lbl.setFixedWidth(55)
            row.addWidget(lbl)
            cols_edit = QLineEdit()
            cols_edit.setPlaceholderText("col1, col2, ...")
            cols_edit.setText(
                ", ".join(self.step.params.get("columns", []))
            )
            cols_edit.textChanged.connect(
                lambda t: self.step.params.__setitem__(
                    "columns",
                    [c.strip() for c in t.split(",") if c.strip()],
                )
            )
            row.addWidget(cols_edit)
            layout.addLayout(row)

        # Duplicates keep strategy
        if tt == TransformType.REMOVE_DUPLICATES:
            row = QHBoxLayout()
            row.setSpacing(6)
            lbl = QLabel("Keep:")
            lbl.setProperty("role", "caption")
            lbl.setFixedWidth(55)
            row.addWidget(lbl)
            keep = QComboBox()
            keep.addItems(["first", "last"])
            keep.setCurrentText(
                self.step.params.get("keep", "first")
            )
            keep.currentTextChanged.connect(
                lambda t: self.step.params.__setitem__("keep", t)
            )
            row.addWidget(keep)
            layout.addLayout(row)

    def get_step(self) -> TransformStep:
        return self.step


class TransformSidebar(QWidget):
    """Sidebar for building a transformation pipeline.

    Signals
    -------
    pipeline_changed(list)
        Emitted with list of TransformStep whenever the pipeline changes.
    """

    pipeline_changed = Signal(list)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._columns: list[str] = []
        self._sample_df: pd.DataFrame | None = None
        self._summary_cards: list[TransformSummaryCard] = []
        # Keep _step_widgets for backwards compatibility with any code inspecting it
        self._step_widgets: list[Any] = []
        self._setup_ui()

    # ── Public API ──────────────────────────────────────────────────

    def set_columns(self, columns: list[str]) -> None:
        """Update available columns for transform configuration."""
        self._columns = columns

    def set_sample_data(self, df: pd.DataFrame | None) -> None:
        """Provide a sample dataframe for live previews in modal dialogs."""
        self._sample_df = df

    def set_sensitive_columns(
        self, sensitive: list[SensitiveColumn]
    ) -> None:
        """Show quick-action buttons for detected sensitive columns."""
        for i in reversed(range(self._sensitive_layout.count())):
            widget = self._sensitive_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        if not sensitive:
            self._sensitive_section.setVisible(False)
            return

        self._sensitive_section.setVisible(True)

        for sc in sensitive[:6]:
            row = QFrame()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 2, 0, 2)
            row_layout.setSpacing(6)

            lbl = QLabel(f"{sc.column_name}")
            lbl.setProperty("role", "caption")
            lbl.setFixedWidth(100)
            lbl.setToolTip(
                f"Category: {sc.category}\n"
                f"Confidence: {sc.confidence:.0%}\n"
                f"{sc.reason}"
            )
            row_layout.addWidget(lbl)

            action_combo = QComboBox()
            action_combo.setFixedWidth(110)
            actions = ["Ignore", "Mask", "Redact", "Hash", "Pseudonymize"]
            action_combo.addItems(actions)

            action_combo.currentTextChanged.connect(
                lambda action, col=sc.column_name: self._on_sensitive_action(
                    col, action
                )
            )

            suggested = sc.suggested_action.capitalize()
            if suggested in actions:
                action_combo.setCurrentText(suggested)
            else:
                action_combo.setCurrentText("Ignore")

            row_layout.addWidget(action_combo)
            self._sensitive_layout.addWidget(row)

    def get_pipeline(self) -> list[TransformStep]:
        """Return the current pipeline as a list of TransformStep."""
        return [c.step for c in self._summary_cards]

    def add_step(self, step: TransformStep) -> None:
        """Programmatically add a transform step."""
        self._add_card(step)
        self._emit_pipeline()

    def clear_pipeline(self) -> None:
        """Clear all configured transformations."""
        for c in list(self._summary_cards):
            self._remove_card(c)
        self._emit_pipeline()

    # ── Setup ───────────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        self.setFixedWidth(300)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        main_frame = QFrame()
        main_frame.setProperty("role", "card")
        main_layout = QVBoxLayout(main_frame)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(8)

        # Title
        title = QLabel("Transformations")
        title.setProperty("role", "subheading")
        main_layout.addWidget(title)

        sep = QFrame()
        sep.setProperty("role", "separator")
        sep.setFrameShape(QFrame.Shape.HLine)
        main_layout.addWidget(sep)

        # Categorized Add Transformation Button & Dropdown
        add_row = QHBoxLayout()
        add_row.setSpacing(6)

        self._transform_combo = QComboBox()
        categories: dict[str, list[TransformType]] = {}
        for tt, info in TRANSFORM_INFO.items():
            cat = info.get("category", "Other")
            categories.setdefault(cat, []).append(tt)

        for cat, types in categories.items():
            for tt in types:
                info = TRANSFORM_INFO[tt]
                self._transform_combo.addItem(f"{info['name']}", tt)

        add_row.addWidget(self._transform_combo, stretch=1)

        add_btn = QPushButton("+ Add")
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.setMinimumHeight(30)
        add_btn.setProperty("role", "primary")
        add_btn.clicked.connect(self._on_add)
        add_row.addWidget(add_btn)

        main_layout.addLayout(add_row)

        # Sensitive columns section
        self._sensitive_section = QFrame()
        sens_layout = QVBoxLayout(self._sensitive_section)
        sens_layout.setContentsMargins(0, 6, 0, 0)
        sens_layout.setSpacing(4)
        sens_title = QLabel("⚠ Sensitive Columns")
        sens_title.setProperty("role", "caption")
        sens_title.setStyleSheet("color: #FBBF24; font-weight: 600;")
        sens_layout.addWidget(sens_title)
        self._sensitive_layout = QVBoxLayout()
        self._sensitive_layout.setSpacing(2)
        sens_layout.addLayout(self._sensitive_layout)
        self._sensitive_section.setVisible(False)
        main_layout.addWidget(self._sensitive_section)

        # Pipeline steps scroll area
        pipeline_label = QLabel("Pipeline")
        pipeline_label.setProperty("role", "caption")
        main_layout.addWidget(pipeline_label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._steps_container = QWidget()
        self._steps_layout = QVBoxLayout(self._steps_container)
        self._steps_layout.setContentsMargins(0, 0, 0, 0)
        self._steps_layout.setSpacing(6)
        self._steps_layout.addStretch()
        scroll.setWidget(self._steps_container)
        main_layout.addWidget(scroll, stretch=1)

        # Clear pipeline button (if steps exist)
        clear_btn = QPushButton("🗑 Clear All Transforms")
        clear_btn.setProperty("role", "ghost")
        clear_btn.setFixedHeight(26)
        clear_btn.clicked.connect(self.clear_pipeline)
        main_layout.addWidget(clear_btn)

        # Summary
        self._summary_label = QLabel("No transforms configured")
        self._summary_label.setProperty("role", "caption")
        self._summary_label.setWordWrap(True)
        main_layout.addWidget(self._summary_label)

        root.addWidget(main_frame)

    # ── Slots ───────────────────────────────────────────────────────

    def _on_add(self) -> None:
        tt = self._transform_combo.currentData()
        if tt is None:
            return
        self._open_modal_for_transform(tt)

    def _open_modal_for_transform(
        self,
        tt: TransformType,
        existing_step: TransformStep | None = None,
    ) -> None:
        dialog = TransformConfigDialog(
            transform_type=tt,
            available_columns=self._columns,
            sample_df=self._sample_df,
            existing_step=existing_step,
            parent=self,
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            if existing_step:
                # Remove old card when editing
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
            for c in list(self._summary_cards):
                if (
                    c.step.params.get("column") == column
                    and c.step.transform_type
                    in {
                        TransformType.MASK_COLUMN,
                        TransformType.REDACT_COLUMN,
                        TransformType.HASH_COLUMN,
                        TransformType.PSEUDONYMIZE_COLUMN,
                    }
                ):
                    self._remove_card(c)
            self._emit_pipeline()
            return

        tt = _PRIVACY_ACTIONS.get(action_lower)
        if tt is None:
            return

        for c in self._summary_cards:
            if (
                c.step.transform_type == tt
                and c.step.params.get("column") == column
            ):
                return

        # Remove any existing privacy card for this column before adding the new action
        for c in list(self._summary_cards):
            if (
                c.step.params.get("column") == column
                and c.step.transform_type
                in {
                    TransformType.MASK_COLUMN,
                    TransformType.REDACT_COLUMN,
                    TransformType.HASH_COLUMN,
                    TransformType.PSEUDONYMIZE_COLUMN,
                }
            ):
                self._remove_card(c)

        step = TransformStep(
            transform_type=tt,
            params={"column": column},
        )
        self._add_card(step)
        self._emit_pipeline()

    def _add_card(self, step: TransformStep) -> None:
        card = TransformSummaryCard(step)
        card.edit_requested.connect(self._on_edit_requested)
        card.remove_requested.connect(self._on_remove_requested)
        self._summary_cards.append(card)
        self._steps_layout.insertWidget(
            self._steps_layout.count() - 1, card
        )

    def _remove_card(self, card: TransformSummaryCard) -> None:
        if card in self._summary_cards:
            self._summary_cards.remove(card)
            self._steps_layout.removeWidget(card)
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
        if count == 0:
            self._summary_label.setText("No transforms configured")
        else:
            self._summary_label.setText(
                f"{count} transform{'s' if count != 1 else ''} in pipeline"
            )
        self.pipeline_changed.emit(pipeline)

