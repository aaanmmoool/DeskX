"""Unit tests for DataFrameModel and headerData."""

import pandas as pd
from PySide6.QtCore import Qt
from deskx.gui.widgets.file_table import DataFrameModel


def test_header_data_badges_and_tooltips():
    df = pd.DataFrame({
        "Name": ["Alice", None],
        "Age": [30, 25],
    })
    model = DataFrameModel()
    model.update_dataframe(df)

    display_0 = model.headerData(0, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)
    assert "ABC" in display_0
    assert "1 empty" in display_0

    display_1 = model.headerData(1, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)
    assert "123" in display_1

    tooltip_0 = model.headerData(0, Qt.Orientation.Horizontal, Qt.ItemDataRole.ToolTipRole)
    assert "Missing Values: 1 / 2 rows" in tooltip_0
