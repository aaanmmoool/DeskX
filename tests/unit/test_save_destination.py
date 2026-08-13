"""Tests for the save-destination helpers and dialog.

These cover the promise the dialog makes to the user: the source file
can never be the destination, an existing output is never silently
replaced, and the file format is preserved.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

from deskx.core.utils import next_available_path, targets_same_file
from deskx.gui.widgets import save_destination_dialog as save_dialog_module
from deskx.gui.widgets.save_destination_dialog import SaveDestinationDialog


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture(autouse=True)
def isolated_settings(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Point the dialog's "last used folder" memory at a throwaway file.

    Without this the dialog reads the real per-user store, so these
    tests would pass on a clean machine and fail on one where somebody
    had already saved a file somewhere.
    """
    ini = tmp_path / "settings.ini"

    def _scoped(*_args, **_kwargs) -> QSettings:
        return QSettings(str(ini), QSettings.Format.IniFormat)

    monkeypatch.setattr(save_dialog_module, "QSettings", _scoped)


@pytest.fixture
def source_file(tmp_path: Path) -> Path:
    path = tmp_path / "customers.csv"
    path.write_text("id,email\n1,a@example.com\n", encoding="utf-8")
    return path


# ── Pure helpers ────────────────────────────────────────────────────


class TestTargetsSameFile:
    def test_identical_paths_match(self, tmp_path: Path):
        path = tmp_path / "data.csv"
        assert targets_same_file(path, path)

    def test_relative_and_absolute_match(self, tmp_path: Path):
        path = tmp_path / "data.csv"
        assert targets_same_file(path, Path(str(path).replace("\\", "/")))

    def test_case_difference_matches_on_windows(self, tmp_path: Path):
        import os

        first = tmp_path / "Data.csv"
        second = tmp_path / "data.csv"
        expected = os.path.normcase("A") == os.path.normcase("a")
        assert targets_same_file(first, second) is expected

    def test_different_files_do_not_match(self, tmp_path: Path):
        assert not targets_same_file(tmp_path / "a.csv", tmp_path / "b.csv")


class TestNextAvailablePath:
    def test_free_path_is_returned_unchanged(self, tmp_path: Path):
        target = tmp_path / "out.csv"
        assert next_available_path(target) == target

    def test_existing_path_gets_version_two(self, tmp_path: Path):
        target = tmp_path / "out.csv"
        target.write_text("x", encoding="utf-8")
        assert next_available_path(target).name == "out (2).csv"

    def test_versions_increment(self, tmp_path: Path):
        (tmp_path / "out.csv").write_text("x", encoding="utf-8")
        (tmp_path / "out (2).csv").write_text("x", encoding="utf-8")
        assert next_available_path(tmp_path / "out.csv").name == "out (3).csv"

    def test_suffix_is_preserved(self, tmp_path: Path):
        target = tmp_path / "book.xlsx"
        target.write_text("x", encoding="utf-8")
        assert next_available_path(target).suffix == ".xlsx"


# ── Dialog behaviour ────────────────────────────────────────────────


class TestSaveDestinationDialog:
    def test_defaults_to_a_sanitized_sibling(self, qapp, source_file: Path):
        dialog = SaveDestinationDialog(source_file)
        destination = dialog.destination()
        assert destination is not None
        assert destination.filename == "customers_sanitized.csv"
        assert destination.save_pipeline is False
        assert dialog.primary_button.isEnabled()
        dialog.deleteLater()

    def test_pipeline_option_is_available_when_steps_exist(
        self, qapp, source_file: Path
    ):
        dialog = SaveDestinationDialog(source_file, pipeline_step_count=3)
        assert dialog._save_pipeline_check.isEnabled()

        dialog._save_pipeline_check.setChecked(True)
        destination = dialog.destination()

        assert destination is not None
        assert destination.save_pipeline is True
        dialog.deleteLater()

    def test_pipeline_option_is_disabled_without_steps(
        self, qapp, source_file: Path
    ):
        dialog = SaveDestinationDialog(source_file)
        assert not dialog._save_pipeline_check.isEnabled()
        assert not dialog._save_pipeline_check.isChecked()
        dialog.deleteLater()

    def test_source_path_is_rejected(self, qapp, source_file: Path):
        dialog = SaveDestinationDialog(source_file)
        dialog._filename_edit.setText(source_file.name)
        assert not dialog.primary_button.isEnabled()
        assert dialog.destination() is None
        dialog.deleteLater()

    def test_empty_filename_is_rejected(self, qapp, source_file: Path):
        dialog = SaveDestinationDialog(source_file)
        dialog._filename_edit.setText("")
        assert not dialog.primary_button.isEnabled()
        dialog.deleteLater()

    def test_format_change_is_rejected(self, qapp, source_file: Path):
        dialog = SaveDestinationDialog(source_file)
        dialog._filename_edit.setText("customers_sanitized.xlsx")
        assert not dialog.primary_button.isEnabled()
        dialog.deleteLater()

    def test_missing_folder_is_rejected(self, qapp, source_file: Path, tmp_path: Path):
        dialog = SaveDestinationDialog(source_file)
        dialog._location_edit.setText(str(tmp_path / "nowhere"))
        assert not dialog.primary_button.isEnabled()
        dialog.deleteLater()

    def test_existing_output_offers_a_new_version(self, qapp, source_file: Path):
        (source_file.parent / "customers_sanitized.csv").write_text(
            "old", encoding="utf-8"
        )
        dialog = SaveDestinationDialog(source_file)
        dialog._location_edit.setText(str(source_file.parent))

        assert dialog._conflict_card.isVisibleTo(dialog)
        destination = dialog.destination()
        assert destination is not None
        assert destination.filename == "customers_sanitized (2).csv"
        assert destination.replaced_existing is False
        dialog.deleteLater()

    def test_replace_is_explicit(self, qapp, source_file: Path):
        existing = source_file.parent / "customers_sanitized.csv"
        existing.write_text("old", encoding="utf-8")

        dialog = SaveDestinationDialog(source_file)
        dialog._location_edit.setText(str(source_file.parent))
        dialog._replace_radio.setChecked(True)
        dialog._revalidate()

        destination = dialog.destination()
        assert destination is not None
        assert destination.output_path == existing
        assert destination.replaced_existing is True
        dialog.deleteLater()

    def test_missing_extension_is_added_back(self, qapp, source_file: Path):
        dialog = SaveDestinationDialog(source_file)
        dialog._filename_edit.setText("clean_customers")
        destination = dialog.destination()
        assert destination is not None
        assert destination.filename == "clean_customers.csv"
        dialog.deleteLater()
