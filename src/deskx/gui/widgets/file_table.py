"""Data table view and model.

Provides :class:`DataFrameModel` (a ``QAbstractTableModel`` backed by
a Pandas DataFrame) and :class:`FileTableView` (a styled
``QTableView``).  Used by the Preview page.

Improvements:
- Column letter headers (A, B, C...) in row header
- Row numbers in vertical header
- NaN cells displayed as grey italic "—"
- Better column auto-sizing
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from PySide6.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    Qt,
)
from PySide6.QtGui import QBrush, QColor, QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QTableView,
)


def _col_letter(index: int) -> str:
    """Convert 0-based index → spreadsheet column letter (A, B, ..., Z, AA, AB...)."""
    result = ""
    while True:
        result = chr(65 + index % 26) + result
        index = index // 26 - 1
        if index < 0:
            break
    return result


class DataFrameModel(QAbstractTableModel):
    """Qt table model backed by a Pandas DataFrame."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._df = pd.DataFrame()

    # ── Public API ──────────────────────────────────────────────────

    def update_dataframe(self, df: pd.DataFrame) -> None:
        """Replace the backing DataFrame and refresh the view."""
        self.beginResetModel()
        self._df = df.reset_index(drop=True)
        self.endResetModel()

    @property
    def dataframe(self) -> pd.DataFrame:
        return self._df

    # ── QAbstractTableModel overrides ───────────────────────────────

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._df)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._df.columns)

    def data(
        self,
        index: QModelIndex,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if not index.isValid():
            return None

        value = self._df.iat[index.row(), index.column()]

        if role == Qt.ItemDataRole.DisplayRole:
            if pd.isna(value):
                return "—"
            return str(value)

        if role == Qt.ItemDataRole.ForegroundRole:
            if pd.isna(value):
                return QBrush(QColor("#6B6F7E"))
            return None

        if role == Qt.ItemDataRole.FontRole:
            if pd.isna(value):
                font = QFont()
                font.setItalic(True)
                return font
            return None

        if role == Qt.ItemDataRole.ToolTipRole:
            if pd.isna(value):
                return "Missing value (NaN)"
            return str(value)

        return None

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if orientation == Qt.Orientation.Horizontal:
            if section >= len(self._df.columns):
                return None
            col_name = str(self._df.columns[section])
            letter = _col_letter(section)

            if role == Qt.ItemDataRole.DisplayRole:
                dtype = str(self._df[col_name].dtype)
                badge = (
                    "ABC"
                    if "object" in dtype or "str" in dtype
                    else (
                        "123"
                        if "int" in dtype or "float" in dtype
                        else ("📅" if "datetime" in dtype else "•")
                    )
                )
                missing = self._df[col_name].isna().sum()
                missing_text = f" [{missing} empty]" if missing > 0 else ""
                return f"{letter}  {col_name}  ({badge}){missing_text}"

            if role == Qt.ItemDataRole.ToolTipRole:
                s = self._df[col_name]
                missing = s.isna().sum()
                return (
                    f"Column: {col_name}\n"
                    f"Data Type: {s.dtype}\n"
                    f"Missing Values: {missing} / {len(s)} rows\n"
                    f"Unique Values: {s.nunique()}"
                )

        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Vertical:
            return str(section + 1)

        return None


class FileTableView(QTableView):
    """Pre-styled table view for file data preview."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.setShowGrid(True)
        self.setSortingEnabled(True)
        self.setWordWrap(False)

        # Horizontal header
        h = self.horizontalHeader()
        h.setStretchLastSection(True)
        h.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        h.setMinimumSectionSize(80)
        h.setDefaultSectionSize(130)

        # Vertical header — show row numbers
        v = self.verticalHeader()
        v.setVisible(True)
        v.setDefaultSectionSize(28)
        v.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        v.setMinimumWidth(40)

    def setModel(self, model) -> None:
        """Override to auto-resize columns after setting model."""
        super().setModel(model)
        if model and model.columnCount() > 0:
            self._auto_resize_columns()

    def _auto_resize_columns(self) -> None:
        """Resize columns to fit content, with a max width cap."""
        header = self.horizontalHeader()
        for col in range(self.model().columnCount()):
            header.setSectionResizeMode(
                col, QHeaderView.ResizeMode.ResizeToContents
            )
        # After measuring, switch back to interactive
        for col in range(self.model().columnCount()):
            width = min(header.sectionSize(col), 300)
            header.setSectionResizeMode(
                col, QHeaderView.ResizeMode.Interactive
            )
            header.resizeSection(col, width)
        # Always stretch last
        header.setStretchLastSection(True)
