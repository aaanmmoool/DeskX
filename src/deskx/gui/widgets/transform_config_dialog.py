"""Modal configuration dialog for data transformations.

Replaces cramped inline sidebar forms with a spacious modal window:
* Left Panel: Educational context (friendly title, explanation,
  ASCII example, when to use, and prominent warning alert).
* Right Panel: Column selector, parameter inputs, and live sample preview.
"""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from deskx.processing.pipeline import TransformStep, TransformType, execute_pipeline
from deskx.processing.transform_catalog import get_transform_metadata

logger = logging.getLogger(__name__)


class TransformConfigDialog(QDialog):
    """Modal window to configure a transformation step with rich education and preview."""

    def __init__(
        self,
        transform_type: TransformType,
        available_columns: list[str],
        sample_df: pd.DataFrame | None = None,
        existing_step: TransformStep | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.transform_type = transform_type
        self.available_columns = available_columns
        self.sample_df = sample_df.head(5).copy() if sample_df is not None else None
        self.existing_step = existing_step
        self.metadata = get_transform_metadata(transform_type)

        self.column_checkboxes: list[QCheckBox] = []
        self.param_widgets: dict[str, Any] = {}

        self.setWindowTitle(f"Configure Transformation — {self.metadata.friendly_name}")
        self.setMinimumSize(860, 620)
        self.resize(920, 680)

        self._setup_ui()
        self._load_existing_values()
        self._update_preview()

    # ── Public API ──────────────────────────────────────────────────

    def get_steps(self) -> list[TransformStep]:
        """Return the configured TransformStep(s)."""
        tt = self.transform_type
        params = self._gather_params()

        # Some transforms do not target specific columns
        non_column_transforms = {
            TransformType.TRIM_WHITESPACE,
            TransformType.REMOVE_EMPTY_ROWS,
            TransformType.REMOVE_EMPTY_COLUMNS,
            TransformType.REMOVE_DUPLICATES,
            TransformType.REMOVE_COLUMNS,
            TransformType.RENAME_COLUMNS,
            TransformType.REORDER_COLUMNS,
        }

        if tt in non_column_transforms:
            return [TransformStep(transform_type=tt, params=params)]

        # For column-specific transforms, generate one step per checked column
        selected_cols = [
            cb.property("col_name")
            for cb in self.column_checkboxes
            if cb.isChecked()
        ]
        if not selected_cols and self.available_columns:
            # Fallback if none checked: use first available
            selected_cols = [self.available_columns[0]]

        steps = []
        for col in selected_cols:
            step_params = dict(params)
            step_params["column"] = col
            steps.append(TransformStep(transform_type=tt, params=step_params))
        return steps

    # ── UI Setup ────────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(20)

        # ═══ Left Panel: Educational Context ════════════════════════
        left_card = QFrame()
        left_card.setProperty("role", "card")
        left_card.setFixedWidth(340)
        left_layout = QVBoxLayout(left_card)
        left_layout.setContentsMargins(18, 18, 18, 18)
        left_layout.setSpacing(12)

        title = QLabel(self.metadata.friendly_name)
        title.setProperty("role", "heading")
        title.setStyleSheet("font-size: 20px; font-weight: 600;")
        left_layout.addWidget(title)

        cat_badge = QLabel(f"Category: {self.metadata.category}")
        cat_badge.setProperty("role", "caption")
        cat_badge.setStyleSheet("color: #6C72CB; font-weight: 600; text-transform: uppercase;")
        left_layout.addWidget(cat_badge)

        one_liner = QLabel(self.metadata.one_liner)
        one_liner.setProperty("role", "subheading")
        one_liner.setWordWrap(True)
        left_layout.addWidget(one_liner)

        what_title = QLabel("What it does")
        what_title.setStyleSheet("font-weight: 600; font-size: 13px; margin-top: 6px;")
        left_layout.addWidget(what_title)

        what_desc = QLabel(self.metadata.what_it_does)
        what_desc.setWordWrap(True)
        what_desc.setProperty("role", "caption")
        left_layout.addWidget(what_desc)

        ex_title = QLabel("Example")
        ex_title.setStyleSheet("font-weight: 600; font-size: 13px; margin-top: 6px;")
        left_layout.addWidget(ex_title)

        ex_box = QTextEdit()
        ex_box.setReadOnly(True)
        ex_box.setText(self.metadata.example_visual)
        ex_box.setMaximumHeight(115)
        ex_box.setStyleSheet(
            "background-color: #0F1117; color: #34D399; font-family: 'Consolas', monospace; font-size: 12px; padding: 8px; border-radius: 6px;"
        )
        left_layout.addWidget(ex_box)

        when_title = QLabel("When to use")
        when_title.setStyleSheet("font-weight: 600; font-size: 13px; margin-top: 6px;")
        left_layout.addWidget(when_title)

        when_desc = QLabel(self.metadata.when_to_use)
        when_desc.setWordWrap(True)
        when_desc.setProperty("role", "caption")
        left_layout.addWidget(when_desc)

        # Warning Alert Box
        warn_box = QFrame()
        warn_box.setObjectName("warningBox")
        warn_box.setStyleSheet(
            "background-color: rgba(251, 191, 36, 0.12); border: 1px solid #FBBF24; border-radius: 8px; padding: 10px;"
        )
        warn_layout = QVBoxLayout(warn_box)
        warn_layout.setContentsMargins(10, 8, 10, 8)
        warn_layout.setSpacing(4)
        warn_header = QLabel("⚠ Potential Warning")
        warn_header.setStyleSheet("color: #FBBF24; font-weight: 600; font-size: 12px;")
        warn_layout.addWidget(warn_header)
        warn_text = QLabel(self.metadata.warning)
        warn_text.setWordWrap(True)
        warn_text.setStyleSheet("color: #FEE2E2; font-size: 12px;")
        warn_layout.addWidget(warn_text)
        left_layout.addWidget(warn_box)

        left_layout.addStretch()
        root.addWidget(left_card)

        # ═══ Right Panel: Configuration & Preview ═══════════════════
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(16)

        # Section 1: Column Selector (if applicable)
        if self._needs_column_selector():
            col_section = QFrame()
            col_section.setProperty("role", "card")
            col_layout = QVBoxLayout(col_section)
            col_layout.setContentsMargins(14, 12, 14, 12)
            col_layout.setSpacing(8)

            col_header = QHBoxLayout()
            col_lbl = QLabel("1. Select Target Column(s)")
            col_lbl.setStyleSheet("font-weight: 600; font-size: 14px;")
            col_header.addWidget(col_lbl)
            col_header.addStretch()

            select_all_btn = QPushButton("Select All")
            select_all_btn.setProperty("role", "ghost")
            select_all_btn.setFixedHeight(26)
            select_all_btn.clicked.connect(self._select_all_cols)
            col_header.addWidget(select_all_btn)

            deselect_all_btn = QPushButton("Deselect All")
            deselect_all_btn.setProperty("role", "ghost")
            deselect_all_btn.setFixedHeight(26)
            deselect_all_btn.clicked.connect(self._deselect_all_cols)
            col_header.addWidget(deselect_all_btn)
            col_layout.addLayout(col_header)

            col_scroll = QScrollArea()
            col_scroll.setWidgetResizable(True)
            col_scroll.setFrameShape(QFrame.Shape.NoFrame)
            col_scroll.setMaximumHeight(140)

            cb_container = QWidget()
            cb_layout = QVBoxLayout(cb_container)
            cb_layout.setContentsMargins(4, 4, 4, 4)
            cb_layout.setSpacing(4)

            for col in self.available_columns:
                cb = QCheckBox(col)
                cb.setChecked(self._is_col_initially_checked(col))
                cb.setProperty("col_name", col)
                cb.stateChanged.connect(lambda: self._update_preview())
                cb_layout.addWidget(cb)
                self.column_checkboxes.append(cb)

            cb_layout.addStretch()
            col_scroll.setWidget(cb_container)
            col_layout.addWidget(col_scroll)
            right_layout.addWidget(col_section)

        # Section 2: Parameter Inputs
        param_section = QFrame()
        param_section.setProperty("role", "card")
        param_layout = QVBoxLayout(param_section)
        param_layout.setContentsMargins(14, 12, 14, 12)
        param_layout.setSpacing(10)

        param_lbl = QLabel(
            "2. Transformation Settings" if self._needs_column_selector() else "1. Transformation Settings"
        )
        param_lbl.setStyleSheet("font-weight: 600; font-size: 14px;")
        param_layout.addWidget(param_lbl)

        self._build_param_controls(param_layout)
        right_layout.addWidget(param_section)

        # Section 3: Live Sample Preview
        preview_section = QFrame()
        preview_section.setProperty("role", "card")
        preview_layout = QVBoxLayout(preview_section)
        preview_layout.setContentsMargins(14, 12, 14, 12)
        preview_layout.setSpacing(8)

        prev_lbl = QLabel("Live Sample Preview (First 5 Rows)")
        prev_lbl.setStyleSheet("font-weight: 600; font-size: 14px;")
        preview_layout.addWidget(prev_lbl)

        self.preview_table = QTableWidget()
        self.preview_table.setMaximumHeight(160)
        self.preview_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Interactive
        )
        preview_layout.addWidget(self.preview_table)
        right_layout.addWidget(preview_section, stretch=1)

        # Section 4: Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        done_btn = QPushButton("Done — Add to Pipeline")
        done_btn.setProperty("role", "primary")
        done_btn.clicked.connect(self.accept)
        btn_layout.addWidget(done_btn)
        right_layout.addLayout(btn_layout)

        root.addWidget(right_panel, stretch=1)

    # ── Helpers ─────────────────────────────────────────────────────

    def _needs_column_selector(self) -> bool:
        return self.transform_type not in {
            TransformType.TRIM_WHITESPACE,
            TransformType.REMOVE_EMPTY_ROWS,
            TransformType.REMOVE_EMPTY_COLUMNS,
            TransformType.REMOVE_DUPLICATES,
            TransformType.REMOVE_COLUMNS,
            TransformType.RENAME_COLUMNS,
            TransformType.REORDER_COLUMNS,
        }

    def _is_col_initially_checked(self, col: str) -> bool:
        if self.existing_step:
            return self.existing_step.params.get("column") == col
        return True

    def _select_all_cols(self) -> None:
        for cb in self.column_checkboxes:
            cb.blockSignals(True)
            cb.setChecked(True)
            cb.blockSignals(False)
        self._update_preview()

    def _deselect_all_cols(self) -> None:
        for cb in self.column_checkboxes:
            cb.blockSignals(True)
            cb.setChecked(False)
            cb.blockSignals(False)
        self._update_preview()

    def _build_param_controls(self, layout: QVBoxLayout) -> None:
        tt = self.transform_type

        if tt == TransformType.FILL_MISSING:
            row = QHBoxLayout()
            row.addWidget(QLabel("Strategy:"))
            combo = QComboBox()
            combo.addItems(["value", "mean", "median", "mode", "forward", "backward", "drop"])
            if self.existing_step:
                combo.setCurrentText(self.existing_step.params.get("strategy", "value"))
            combo.currentTextChanged.connect(lambda: self._update_preview())
            row.addWidget(combo)
            layout.addLayout(row)
            self.param_widgets["strategy"] = combo

            val_row = QHBoxLayout()
            val_row.addWidget(QLabel("Fallback Value (for 'value' strategy):"))
            val_edit = QLineEdit()
            if self.existing_step:
                val_edit.setText(str(self.existing_step.params.get("value", "")))
            val_edit.textChanged.connect(lambda: self._update_preview())
            val_row.addWidget(val_edit)
            layout.addLayout(val_row)
            self.param_widgets["value"] = val_edit

        elif tt == TransformType.MASK_COLUMN:
            row = QHBoxLayout()
            row.addWidget(QLabel("Show last N visible characters:"))
            spin = QSpinBox()
            spin.setRange(0, 10)
            spin.setValue(int(self.existing_step.params.get("show_last", 4)) if self.existing_step else 4)
            spin.valueChanged.connect(lambda: self._update_preview())
            row.addWidget(spin)
            layout.addLayout(row)
            self.param_widgets["show_last"] = spin

        elif tt == TransformType.REDACT_COLUMN:
            row = QHBoxLayout()
            row.addWidget(QLabel("Replacement text:"))
            edit = QLineEdit("[REDACTED]")
            if self.existing_step:
                edit.setText(str(self.existing_step.params.get("replacement", "[REDACTED]")))
            edit.textChanged.connect(lambda: self._update_preview())
            row.addWidget(edit)
            layout.addLayout(row)
            self.param_widgets["replacement"] = edit

        elif tt == TransformType.PSEUDONYMIZE_COLUMN:
            row = QHBoxLayout()
            row.addWidget(QLabel("Fake name prefix:"))
            edit = QLineEdit("Person_")
            if self.existing_step:
                edit.setText(str(self.existing_step.params.get("prefix", "Person_")))
            edit.textChanged.connect(lambda: self._update_preview())
            row.addWidget(edit)
            layout.addLayout(row)
            self.param_widgets["prefix"] = edit

        elif tt == TransformType.GENERALIZE_COLUMN:
            row = QHBoxLayout()
            row.addWidget(QLabel("Round numbers/ages to multiple of:"))
            spin = QSpinBox()
            spin.setRange(1, 1000)
            spin.setValue(int(self.existing_step.params.get("round_to", 10)) if self.existing_step else 10)
            spin.valueChanged.connect(lambda: self._update_preview())
            row.addWidget(spin)
            layout.addLayout(row)
            self.param_widgets["round_to"] = spin

        elif tt == TransformType.SUPPRESS_LOW_COUNTS:
            row = QHBoxLayout()
            row.addWidget(QLabel("Suppress categories with fewer than N items:"))
            spin = QSpinBox()
            spin.setRange(1, 100)
            spin.setValue(int(self.existing_step.params.get("threshold", 5)) if self.existing_step else 5)
            spin.valueChanged.connect(lambda: self._update_preview())
            row.addWidget(spin)
            layout.addLayout(row)
            self.param_widgets["threshold"] = spin

            r_row = QHBoxLayout()
            r_row.addWidget(QLabel("Replacement label for rare categories:"))
            r_edit = QLineEdit("Other")
            if self.existing_step:
                r_edit.setText(str(self.existing_step.params.get("replacement", "Other")))
            r_edit.textChanged.connect(lambda: self._update_preview())
            r_row.addWidget(r_edit)
            layout.addLayout(r_row)
            self.param_widgets["replacement"] = r_edit

        elif tt == TransformType.REMOVE_DUPLICATES:
            row = QHBoxLayout()
            row.addWidget(QLabel("Keep duplicate:"))
            combo = QComboBox()
            combo.addItems(["first", "last"])
            if self.existing_step:
                combo.setCurrentText(str(self.existing_step.params.get("keep", "first")))
            combo.currentTextChanged.connect(lambda: self._update_preview())
            row.addWidget(combo)
            layout.addLayout(row)
            self.param_widgets["keep"] = combo

        elif tt == TransformType.REMOVE_COLUMNS:
            row = QHBoxLayout()
            row.addWidget(QLabel("Columns to remove (comma separated):"))
            edit = QLineEdit()
            edit.setPlaceholderText("col1, col2")
            if self.existing_step:
                edit.setText(", ".join(self.existing_step.params.get("columns", [])))
            edit.textChanged.connect(lambda: self._update_preview())
            row.addWidget(edit)
            layout.addLayout(row)
            self.param_widgets["columns"] = edit

        elif tt == TransformType.FILTER_ROWS:
            row = QHBoxLayout()
            row.addWidget(QLabel("Operator:"))
            op_combo = QComboBox()
            op_combo.addItems(["==", "!=", ">", "<", ">=", "<=", "contains", "not_contains"])
            if self.existing_step:
                op_combo.setCurrentText(str(self.existing_step.params.get("operator", "==")))
            op_combo.currentTextChanged.connect(lambda: self._update_preview())
            row.addWidget(op_combo)
            layout.addLayout(row)
            self.param_widgets["operator"] = op_combo

            val_row = QHBoxLayout()
            val_row.addWidget(QLabel("Value to match:"))
            val_edit = QLineEdit()
            if self.existing_step:
                val_edit.setText(str(self.existing_step.params.get("value", "")))
            val_edit.textChanged.connect(lambda: self._update_preview())
            val_row.addWidget(val_edit)
            layout.addLayout(val_row)
            self.param_widgets["value"] = val_edit

        elif tt == TransformType.REPLACE_VALUES:
            f_row = QHBoxLayout()
            f_row.addWidget(QLabel("Find text:"))
            f_edit = QLineEdit()
            if self.existing_step:
                f_edit.setText(str(self.existing_step.params.get("find", "")))
            f_edit.textChanged.connect(lambda: self._update_preview())
            f_row.addWidget(f_edit)
            layout.addLayout(f_row)
            self.param_widgets["find"] = f_edit

            r_row = QHBoxLayout()
            r_row.addWidget(QLabel("Replace with:"))
            r_edit = QLineEdit()
            if self.existing_step:
                r_edit.setText(str(self.existing_step.params.get("replace", "")))
            r_edit.textChanged.connect(lambda: self._update_preview())
            r_row.addWidget(r_edit)
            layout.addLayout(r_row)
            self.param_widgets["replace"] = r_edit

        else:
            info_lbl = QLabel("No additional parameters required for this transformation.")
            info_lbl.setProperty("role", "caption")
            layout.addWidget(info_lbl)

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
        self.preview_table.setHorizontalHeaderLabels(list(df.columns))

        for row_idx in range(len(df)):
            for col_idx, col_name in enumerate(df.columns):
                val = df.iloc[row_idx, col_idx]
                text_val = "—" if pd.isna(val) else str(val)
                item = QTableWidgetItem(text_val)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.preview_table.setItem(row_idx, col_idx, item)
