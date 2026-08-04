"""Unit test for automatic sensitive column action population in TransformSidebar."""

from __future__ import annotations

import pytest
from PySide6.QtWidgets import QApplication

from deskx.gui.widgets.transform_sidebar import TransformSidebar
from deskx.processing.pipeline import TransformType
from deskx.processing.sensitive_detector import SensitiveColumn


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_set_sensitive_columns_auto_populates_pipeline(qapp):
    sidebar = TransformSidebar()
    sc = SensitiveColumn(
        column_name="Email Address",
        category="email",
        confidence=0.85,
        reason="Looks like email",
        suggested_action="mask",
    )
    sidebar.set_sensitive_columns([sc])
    pipeline = sidebar.get_pipeline()
    assert len(pipeline) == 1
    assert pipeline[0].transform_type == TransformType.MASK_COLUMN
    assert pipeline[0].params.get("column") == "Email Address"
    sidebar.close()


def test_on_sensitive_action_switches_protection(qapp):
    sidebar = TransformSidebar()
    sc = SensitiveColumn(
        column_name="Email Address",
        category="email",
        confidence=0.85,
        reason="Looks like email",
        suggested_action="mask",
    )
    sidebar.set_sensitive_columns([sc])
    assert len(sidebar.get_pipeline()) == 1
    assert sidebar.get_pipeline()[0].transform_type == TransformType.MASK_COLUMN

    # Now switch to Redact
    sidebar._on_sensitive_action("Email Address", "Redact")
    pipeline = sidebar.get_pipeline()
    assert len(pipeline) == 1
    assert pipeline[0].transform_type == TransformType.REDACT_COLUMN

    # Now switch to Ignore
    sidebar._on_sensitive_action("Email Address", "Ignore")
    assert len(sidebar.get_pipeline()) == 0
    sidebar.close()
