"""Unit tests for help dialog, welcome dialog, and sample dataset loader."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

from deskx.gui.widgets.help_dialog import HelpDialog
from deskx.gui.widgets.welcome_dialog import WelcomeDialog
from deskx.gui.main_window import MainWindow
from deskx.samples import get_sample_employee_dataset_path


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_sample_employee_dataset_exists():
    path = get_sample_employee_dataset_path()
    assert path.exists()
    assert path.suffix == ".csv"
    assert "Alice Smith" in path.read_text(encoding="utf-8")


def test_help_dialog_instantiation(qapp):
    dlg = HelpDialog()
    assert "User Guide" in dlg.windowTitle()
    dlg.close()


def test_welcome_dialog_instantiation(qapp):
    dlg = WelcomeDialog()
    assert "Welcome" in dlg.windowTitle()
    assert dlg.load_sample_requested is False
    dlg.close()


def test_main_window_instantiation(qapp):
    win = MainWindow()
    assert win is not None
    assert "DeskX" in win.windowTitle()
    win.close()

