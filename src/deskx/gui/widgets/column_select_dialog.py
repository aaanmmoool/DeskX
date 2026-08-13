"""Column inclusion picker.

Lets the user decide which columns end up in the sanitized copy.
Columns the sensitive-data detector flagged are marked so it is
obvious what is about to be shared.

The dialog edits a copy of the selection and only hands it back when
the user confirms, so cancelling is always safe.
"""

from __future__ import annotations

import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from deskx.gui.theme import SIZE, SPACE, palette
from deskx.gui.theme.icons import Icon, icon_label
from deskx.gui.widgets.components import Badge, Button, Card, label
from deskx.gui.widgets.modal import ModalDialog
from deskx.processing.sensitive_detector import SensitiveColumn


class ColumnSelectDialog(ModalDialog):
    """Choose which columns to keep in the output."""

    def __init__(
        self,
        dataframe: pd.DataFrame,
        selection: dict[str, bool],
        sensitive: list[SensitiveColumn] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            title="Choose columns",
            subtitle="Only the columns you keep are written to the sanitized copy.",
            icon=Icon.COLUMNS,
            width=640,
            primary_text="Apply",
            parent=parent,
        )
        self._df = dataframe
        self._sensitive = {s.column_name: s for s in (sensitive or [])}
        self._checkboxes: dict[str, QCheckBox] = {}

        self._build_toolbar()
        self._build_rows(selection)
        self.content.addStretch()
        self._update_summary()

    # ── Result ──────────────────────────────────────────────────────

    def selection(self) -> dict[str, bool]:
        """Return the chosen include/exclude state for every column."""
        return {name: cb.isChecked() for name, cb in self._checkboxes.items()}

    # ── Construction ────────────────────────────────────────────────

    def _build_toolbar(self) -> None:
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(SPACE.sm)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Filter columns…")
        self._search.setClearButtonEnabled(True)
        self._search.setMinimumHeight(SIZE.control_height)
        self._search.textChanged.connect(self._apply_filter)
        row.addWidget(self._search, 1)

        select_all = Button("Select all", role="ghost")
        select_all.clicked.connect(lambda: self._set_all(True))
        row.addWidget(select_all)

        clear = Button("Clear", role="ghost")
        clear.clicked.connect(lambda: self._set_all(False))
        row.addWidget(clear)

        self.content.addLayout(row)

        self._summary = label("", "caption")
        self.content.addWidget(self._summary)

    def _build_rows(self, selection: dict[str, bool]) -> None:
        self._rows_card = Card(padding=SPACE.sm, spacing=SPACE.xxs)
        self._row_widgets: dict[str, QWidget] = {}

        for column in self._df.columns:
            name = str(column)
            row = self._make_row(name, selection.get(name, True))
            self._rows_card.add(row)
            self._row_widgets[name] = row

        self.content.addWidget(self._rows_card)

    def _make_row(self, name: str, checked: bool) -> QWidget:
        series = self._df[name]
        missing = int(series.isna().sum())
        total = len(series)

        row = QFrame()
        row.setProperty("role", "cardFlat")
        layout = QHBoxLayout(row)
        layout.setContentsMargins(SPACE.md, SPACE.sm, SPACE.md, SPACE.sm)
        layout.setSpacing(SPACE.sm)

        checkbox = QCheckBox(name)
        checkbox.setChecked(checked)
        checkbox.setProperty("col_name", name)
        checkbox.stateChanged.connect(lambda *_: self._update_summary())
        checkbox.setToolTip(
            f"Type: {series.dtype}\n"
            f"Missing: {missing} of {total} rows\n"
            f"Unique values: {series.nunique()}"
        )
        layout.addWidget(checkbox, 1)
        self._checkboxes[name] = checkbox

        detected = self._sensitive.get(name)
        if detected is not None:
            flag = Badge(detected.category.replace("_", " ").title(), "warning")
            flag.setToolTip(detected.reason)
            layout.addWidget(flag)

        layout.addWidget(Badge(_type_name(series), "neutral"))

        if missing:
            gap = Badge(f"{missing} empty", "neutral")
            gap.setToolTip(f"{missing} of {total} rows have no value")
            layout.addWidget(gap)

        return row

    # ── Behaviour ───────────────────────────────────────────────────

    def _set_all(self, checked: bool) -> None:
        for name, checkbox in self._checkboxes.items():
            if self._row_widgets[name].isVisible():
                checkbox.blockSignals(True)
                checkbox.setChecked(checked)
                checkbox.blockSignals(False)
        self._update_summary()

    def _apply_filter(self, text: str) -> None:
        needle = text.strip().lower()
        for name, row in self._row_widgets.items():
            row.setVisible(needle in name.lower())

    def _update_summary(self) -> None:
        total = len(self._checkboxes)
        kept = sum(1 for cb in self._checkboxes.values() if cb.isChecked())
        if kept == total:
            self._summary.setText(f"All {total} columns will be included.")
        elif kept == 0:
            self._summary.setText(
                "No columns selected — every column will be kept instead."
            )
        else:
            self._summary.setText(
                f"{kept} of {total} columns will be included "
                f"({total - kept} dropped)."
            )


def _type_name(series: pd.Series) -> str:
    """A short, non-technical label for a column's data type."""
    dtype = str(series.dtype)
    if "int" in dtype or "float" in dtype:
        return "Number"
    if "datetime" in dtype:
        return "Date"
    if "bool" in dtype:
        return "Yes/No"
    return "Text"
