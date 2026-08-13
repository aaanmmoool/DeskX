"""Modal configuration dialog for a single transformation.

Structure (shared with every other DeskX modal via
:class:`~deskx.gui.widgets.modal.ModalDialog`):

* header — friendly name, plain-English one-liner
* explanation — what it does, plus a before/after example
* columns — which fields the transformation applies to
* settings — the transformation's own parameters
* preview — the first five rows, transformed live
* caveat — the catalog's warning, if the change is irreversible

The dialog only *builds* :class:`TransformStep` objects; it never
changes how a transformation is implemented.
"""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QScrollArea,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from deskx.gui.theme import SPACE
from deskx.gui.theme.icons import Icon
from deskx.gui.widgets.components import (
    Button,
    Card,
    InfoNote,
    label,
)
from deskx.gui.widgets.modal import ModalDialog
from deskx.gui.widgets.transform_summary_card import icon_for
from deskx.processing.pipeline import TransformStep, TransformType, execute_pipeline
from deskx.processing.transform_catalog import get_transform_metadata

logger = logging.getLogger(__name__)

# Transformations that operate on the whole table rather than columns.
_NON_COLUMN_TRANSFORMS = frozenset({
    TransformType.TRIM_WHITESPACE,
    TransformType.REMOVE_EMPTY_ROWS,
    TransformType.REMOVE_EMPTY_COLUMNS,
    TransformType.REMOVE_DUPLICATES,
    TransformType.REMOVE_COLUMNS,
    TransformType.RENAME_COLUMNS,
    TransformType.REORDER_COLUMNS,
})

_COLUMNS_PER_ROW = 3


class TransformConfigDialog(ModalDialog):
    """Configure one transformation before adding it to the pipeline."""

    def __init__(
        self,
        transform_type: TransformType,
        available_columns: list[str],
        sample_df: pd.DataFrame | None = None,
        existing_step: TransformStep | None = None,
        parent: QWidget | None = None,
    ) -> None:
        self.transform_type = transform_type
        self.available_columns = available_columns
        self.sample_df = sample_df.head(5).copy() if sample_df is not None else None
        self.existing_step = existing_step
        self.metadata = get_transform_metadata(transform_type)

        self.column_checkboxes: list[QCheckBox] = []
        self.param_widgets: dict[str, Any] = {}

        super().__init__(
            title=self.metadata.friendly_name,
            subtitle=self.metadata.one_liner,
            icon=icon_for(self.metadata),
            width=700,
            primary_text="Done",
            parent=parent,
        )
        self.setWindowTitle(f"Configure — {self.metadata.friendly_name}")

        self._build_explanation()
        if self._needs_column_selector():
            self._build_column_selector()
        self._build_settings()
        self._build_preview()
        self._build_caveat()
        self.content.addStretch()

        self._load_existing_values()
        self._update_preview()

    # ── Public API ──────────────────────────────────────────────────

    def get_steps(self) -> list[TransformStep]:
        """Return the configured :class:`TransformStep` objects."""
        tt = self.transform_type
        params = self._gather_params()

        if tt in _NON_COLUMN_TRANSFORMS:
            return [TransformStep(transform_type=tt, params=params)]

        selected_cols = [
            cb.property("col_name")
            for cb in self.column_checkboxes
            if cb.isChecked()
        ]
        if not selected_cols and self.available_columns:
            # Fallback if none checked: use the first available column.
            selected_cols = [self.available_columns[0]]

        steps = []
        for col in selected_cols:
            step_params = dict(params)
            step_params["column"] = col
            steps.append(TransformStep(transform_type=tt, params=step_params))
        return steps

    # ── Sections ────────────────────────────────────────────────────

    def _build_explanation(self) -> None:
        card = Card(padding=SPACE.lg, spacing=SPACE.sm, variant="inset")
        card.add(label(self.metadata.what_it_does, "body", wrap=True))

        example = QFrame()
        example.setProperty("role", "card")
        row = QHBoxLayout(example)
        row.setContentsMargins(SPACE.md, SPACE.sm + 2, SPACE.md, SPACE.sm + 2)
        row.setSpacing(SPACE.md)

        before = label(self.metadata.example_in, "mono")
        before.setToolTip(self.metadata.example_visual)
        row.addWidget(before, 1)

        arrow = label("→", "body", tone="primary")
        row.addWidget(arrow, 0, Qt.AlignmentFlag.AlignVCenter)

        after = label(self.metadata.example_out, "mono", tone="success")
        after.setToolTip(self.metadata.example_visual)
        row.addWidget(after, 1)

        card.add(example)
        card.add(label(f"When to use   ·   {self.metadata.when_to_use}", "caption", wrap=True))
        self.content.addWidget(card)

    def _build_column_selector(self) -> None:
        self.content.addWidget(label("COLUMNS", "eyebrow"))

        card = Card(padding=SPACE.md, spacing=SPACE.sm)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(SPACE.xs)
        header.addWidget(label("Apply this to", "body"))
        header.addStretch()

        select_all = Button("Select all", role="link")
        select_all.clicked.connect(self._select_all_cols)
        header.addWidget(select_all)

        clear_all = Button("Clear", role="link")
        clear_all.clicked.connect(self._deselect_all_cols)
        header.addWidget(clear_all)
        card.add_layout(header)

        container = QWidget()
        grid = QGridLayout(container)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(SPACE.md)
        grid.setVerticalSpacing(SPACE.xs)

        for index, col in enumerate(self.available_columns):
            checkbox = QCheckBox(str(col))
            checkbox.setChecked(self._is_col_initially_checked(col))
            checkbox.setProperty("col_name", col)
            checkbox.setToolTip(str(col))
            checkbox.stateChanged.connect(lambda *_: self._update_preview())
            grid.addWidget(
                checkbox, index // _COLUMNS_PER_ROW, index % _COLUMNS_PER_ROW
            )
            self.column_checkboxes.append(checkbox)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setMaximumHeight(120)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(container)
        card.add(scroll)

        self.content.addWidget(card)

    def _build_settings(self) -> None:
        rows = QVBoxLayout()
        rows.setContentsMargins(0, 0, 0, 0)
        rows.setSpacing(SPACE.sm)
        self._build_param_controls(rows)

        if not self.param_widgets:
            return

        self.content.addWidget(label("SETTINGS", "eyebrow"))
        card = Card(padding=SPACE.md, spacing=SPACE.sm)
        card.add_layout(rows)
        self.content.addWidget(card)

    def _build_preview(self) -> None:
        if self.sample_df is None or self.sample_df.empty:
            self.preview_table = QTableWidget()
            self.preview_table.setVisible(False)
            return

        self.content.addWidget(label("PREVIEW — FIRST 5 ROWS", "eyebrow"))

        self.preview_table = QTableWidget()
        self.preview_table.setMaximumHeight(158)
        self.preview_table.verticalHeader().setVisible(False)
        self.preview_table.setAlternatingRowColors(True)
        self.preview_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.preview_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Interactive
        )
        self.content.addWidget(self.preview_table)

    def _build_caveat(self) -> None:
        if not self.metadata.warning:
            return
        self.content.addWidget(
            InfoNote(self.metadata.warning, variant="warning", icon=Icon.WARNING)
        )

    # ── Helpers ─────────────────────────────────────────────────────

    def _needs_column_selector(self) -> bool:
        return self.transform_type not in _NON_COLUMN_TRANSFORMS

    def _is_col_initially_checked(self, col: str) -> bool:
        if self.existing_step:
            return self.existing_step.params.get("column") == col
        return True

    def _select_all_cols(self) -> None:
        self._set_all_columns(True)

    def _deselect_all_cols(self) -> None:
        self._set_all_columns(False)

    def _set_all_columns(self, checked: bool) -> None:
        for checkbox in self.column_checkboxes:
            checkbox.blockSignals(True)
            checkbox.setChecked(checked)
            checkbox.blockSignals(False)
        self._update_preview()

    def _load_existing_values(self) -> None:
        """Kept as an explicit hook — controls self-populate on build."""

    def _param_row(
        self,
        layout: QVBoxLayout,
        caption: str,
        widget: QWidget,
        key: str,
    ) -> None:
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(SPACE.md)

        caption_lbl = QLabel(caption)
        caption_lbl.setWordWrap(True)
        caption_lbl.setMinimumWidth(250)
        caption_lbl.setMaximumWidth(280)
        row.addWidget(caption_lbl, 0, Qt.AlignmentFlag.AlignVCenter)

        widget.setMinimumWidth(180)
        row.addWidget(widget, 1)

        layout.addLayout(row)
        self.param_widgets[key] = widget

    def _build_param_controls(self, layout: QVBoxLayout) -> None:
        tt = self.transform_type
        existing = self.existing_step.params if self.existing_step else {}

        if tt == TransformType.FILL_MISSING:
            combo = QComboBox()
            combo.addItems(
                ["value", "mean", "median", "mode", "forward", "backward", "drop"]
            )
            combo.setCurrentText(str(existing.get("strategy", "value")))
            combo.currentTextChanged.connect(lambda: self._update_preview())
            self._param_row(layout, "How should blanks be filled?", combo, "strategy")

            value_edit = QLineEdit(str(existing.get("value", "")))
            value_edit.setPlaceholderText("e.g. Unknown")
            value_edit.textChanged.connect(lambda: self._update_preview())
            self._param_row(
                layout,
                "Fallback value (used by the 'value' strategy)",
                value_edit,
                "value",
            )

        elif tt == TransformType.MASK_COLUMN:
            spin = QSpinBox()
            spin.setRange(0, 10)
            spin.setValue(int(existing.get("show_last", 4)))
            spin.valueChanged.connect(lambda: self._update_preview())
            self._param_row(
                layout, "Characters left visible at the end", spin, "show_last"
            )

        elif tt == TransformType.REDACT_COLUMN:
            edit = QLineEdit(str(existing.get("replacement", "[REDACTED]")))
            edit.textChanged.connect(lambda: self._update_preview())
            self._param_row(layout, "Replace every value with", edit, "replacement")

        elif tt == TransformType.PSEUDONYMIZE_COLUMN:
            edit = QLineEdit(str(existing.get("prefix", "Person_")))
            edit.textChanged.connect(lambda: self._update_preview())
            self._param_row(
                layout, "Label prefix for the anonymous IDs", edit, "prefix"
            )

        elif tt == TransformType.GENERALIZE_COLUMN:
            spin = QSpinBox()
            spin.setRange(1, 1000)
            spin.setValue(int(existing.get("round_to", 10)))
            spin.valueChanged.connect(lambda: self._update_preview())
            self._param_row(layout, "Round numbers to the nearest", spin, "round_to")

        elif tt == TransformType.SUPPRESS_LOW_COUNTS:
            spin = QSpinBox()
            spin.setRange(1, 100)
            spin.setValue(int(existing.get("threshold", 5)))
            spin.valueChanged.connect(lambda: self._update_preview())
            self._param_row(
                layout, "Hide categories with fewer members than", spin, "threshold"
            )

            edit = QLineEdit(str(existing.get("replacement", "Other")))
            edit.textChanged.connect(lambda: self._update_preview())
            self._param_row(layout, "Group those rare values as", edit, "replacement")

        elif tt == TransformType.REMOVE_DUPLICATES:
            combo = QComboBox()
            combo.addItems(["first", "last"])
            combo.setCurrentText(str(existing.get("keep", "first")))
            combo.currentTextChanged.connect(lambda: self._update_preview())
            self._param_row(layout, "Which copy should be kept?", combo, "keep")

        elif tt == TransformType.REMOVE_COLUMNS:
            edit = QLineEdit(", ".join(existing.get("columns", [])))
            edit.setPlaceholderText("Notes, Internal ID")
            edit.textChanged.connect(lambda: self._update_preview())
            self._param_row(
                layout, "Columns to remove (comma separated)", edit, "columns"
            )

        elif tt == TransformType.FILTER_ROWS:
            combo = QComboBox()
            combo.addItems(
                ["==", "!=", ">", "<", ">=", "<=", "contains", "not_contains"]
            )
            combo.setCurrentText(str(existing.get("operator", "==")))
            combo.currentTextChanged.connect(lambda: self._update_preview())
            self._param_row(layout, "Keep rows where the value is", combo, "operator")

            edit = QLineEdit(str(existing.get("value", "")))
            edit.textChanged.connect(lambda: self._update_preview())
            self._param_row(layout, "Compared against", edit, "value")

        elif tt == TransformType.REPLACE_VALUES:
            find_edit = QLineEdit(str(existing.get("find", "")))
            find_edit.textChanged.connect(lambda: self._update_preview())
            self._param_row(layout, "Find this text", find_edit, "find")

            replace_edit = QLineEdit(str(existing.get("replace", "")))
            replace_edit.textChanged.connect(lambda: self._update_preview())
            self._param_row(layout, "Replace it with", replace_edit, "replace")

    def _gather_params(self) -> dict[str, Any]:
        params: dict[str, Any] = {}
        for key, widget in self.param_widgets.items():
            if isinstance(widget, QComboBox):
                params[key] = widget.currentText()
            elif isinstance(widget, QSpinBox):
                params[key] = widget.value()
            elif isinstance(widget, QLineEdit):
                text = widget.text()
                if key == "columns":
                    params[key] = [c.strip() for c in text.split(",") if c.strip()]
                else:
                    params[key] = text
        return params

    def _update_preview(self) -> None:
        if self.sample_df is None or self.sample_df.empty:
            return

        try:
            steps = self.get_steps()
            transformed_df, _ = execute_pipeline(self.sample_df, steps)
        except Exception as exc:
            logger.warning("Preview pipeline failed: %s", exc)
            transformed_df = self.sample_df.copy()

        df = transformed_df
        self.preview_table.clear()
        self.preview_table.setRowCount(len(df))
        self.preview_table.setColumnCount(len(df.columns))
        self.preview_table.setHorizontalHeaderLabels([str(c) for c in df.columns])

        for row_idx in range(len(df)):
            for col_idx in range(len(df.columns)):
                value = df.iloc[row_idx, col_idx]
                text_val = "—" if pd.isna(value) else str(value)
                item = QTableWidgetItem(text_val)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.preview_table.setItem(row_idx, col_idx, item)

        self.preview_table.resizeColumnsToContents()
