"""Unit tests for TransformSummaryCard."""

import pytest
from deskx.processing.pipeline import TransformStep, TransformType
from deskx.gui.widgets.transform_summary_card import TransformSummaryCard


def test_summary_card_formatting(qtbot):
    step = TransformStep(
        transform_type=TransformType.MASK_COLUMN,
        params={"column": "Email", "show_last": 4},
    )
    card = TransformSummaryCard(step)
    qtbot.addWidget(card)

    assert "Mask Email" in card.metadata.friendly_name
    assert card._format_columns() == "Email"
    assert "show_last: 4" in card._format_params()


def test_summary_card_all_columns(qtbot):
    step = TransformStep(
        transform_type=TransformType.TRIM_WHITESPACE,
        params={},
    )
    card = TransformSummaryCard(step)
    qtbot.addWidget(card)

    assert card._format_columns() == "All Columns"
    assert card._format_params() == ""
