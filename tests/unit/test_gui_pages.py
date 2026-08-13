"""Smoke tests for the redesigned screens.

Each page is built, fed the data it would receive at runtime, and
checked for the values a user would read off the screen.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

from deskx.gui.pages.history_page import HistoryPage, _relative_time
from deskx.gui.pages.home_page import HomePage
from deskx.gui.pages.processing_page import ProcessingPage
from deskx.gui.pages.reports_page import ReportsPage
from deskx.gui.pages.results_page import ResultsPage, _steps_summary
from deskx.gui.pages.settings_page import SettingsPage
from deskx.history.recent_files import RecentFilesManager


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def recent(tmp_path: Path) -> RecentFilesManager:
    return RecentFilesManager(storage_path=tmp_path / "recent.json")


@pytest.fixture
def report(tmp_path: Path) -> dict:
    output = tmp_path / "customers_sanitized.csv"
    output.write_text("id\n1\n", encoding="utf-8")
    return {
        "source_path": str(tmp_path / "customers.csv"),
        "output_path": str(output),
        "source_hash": "a" * 64,
        "output_hash": "b" * 64,
        "status": "success",
        "started_at": "2026-08-11T10:00:00+00:00",
        "finished_at": "2026-08-11T10:00:02+00:00",
        "duration_seconds": 2.5,
        "row_count": 12482,
        "column_count": 9,
        "columns_selected": ["id", "email"],
        "error_message": None,
        "pipeline_summary": "✓ Step 1: Trim whitespace\n✓ Step 2: Mask email",
    }


# ── Home ────────────────────────────────────────────────────────────


class TestHomePage:
    def test_stats_start_empty(self, qapp, recent):
        page = HomePage(recent)
        assert page._stat_files._value_lbl.text() == "0"
        assert page._stat_rows._value_lbl.text() == "—"

    def test_recent_file_appears(self, qapp, recent, tmp_path: Path):
        data = tmp_path / "data.csv"
        data.write_text("a\n1\n", encoding="utf-8")
        recent.add(data)

        page = HomePage(recent)
        assert page._stat_files._value_lbl.text() == "1"
        assert page._recent_list.count() == 1

    def test_row_count_comes_from_the_report(self, qapp, recent, report):
        page = HomePage(recent)
        page.refresh(report)
        assert page._stat_rows._value_lbl.text() == "12,482"


# ── Results ─────────────────────────────────────────────────────────


class TestResultsPage:
    def test_report_values_are_shown(self, qapp, report):
        page = ResultsPage()
        page.show_report(report)

        assert page._filename.text() == "customers_sanitized.csv"
        assert page._rows_card._value_lbl.text() == "12,482"
        assert page._cols_card._value_lbl.text() == "9"
        assert page._time_card._value_lbl.text() == "2.50s"

    def test_missing_metrics_hide_their_tiles(self, qapp, report):
        report.pop("row_count")
        page = ResultsPage()
        page.show_report(report)
        assert page._rows_card.isHidden()

    def test_summary_lists_applied_steps(self, report):
        text = _steps_summary(report)
        assert "Trim whitespace" in text
        assert "Mask email" in text

    def test_summary_without_steps_is_honest(self):
        assert "no changes" in _steps_summary({}).lower()


# ── Reports ─────────────────────────────────────────────────────────


class TestReportsPage:
    def test_empty_until_a_job_runs(self, qapp):
        page = ReportsPage()
        assert page._empty.isVisibleTo(page)
        assert page._content.isHidden()

    def test_report_populates_the_page(self, qapp, report):
        page = ReportsPage()
        page.set_report(report, "{}")

        assert page._title.text() == "customers_sanitized.csv"
        assert page._status_badge.text() == "Success"
        assert "Mask email" in page._pipeline_box.toPlainText()


# ── Processing ──────────────────────────────────────────────────────


class TestProcessingPage:
    def test_start_shows_both_filenames(self, qapp, tmp_path: Path):
        page = ProcessingPage()
        page.start(tmp_path / "in.csv", tmp_path / "out.csv", 2)

        assert page._source_lbl.text() == "in.csv"
        assert page._output_lbl.text() == "out.csv"
        assert page._steps_badge.text() == "2 transformations"

    def test_progress_updates_the_bar_and_log(self, qapp, tmp_path: Path):
        page = ProcessingPage()
        page.start(tmp_path / "in.csv", tmp_path / "out.csv", 1)
        page.update_progress(45, "Running transformation pipeline…")

        assert page._progress.value() == 45
        assert page._percent_lbl.text() == "45%"
        assert "pipeline" in page._log_lbl.text()

    def test_cancelling_disables_the_button(self, qapp, tmp_path: Path):
        page = ProcessingPage()
        page.start(tmp_path / "in.csv", tmp_path / "out.csv", 1)
        page.mark_cancelling()
        assert not page._cancel_btn.isEnabled()


# ── History ─────────────────────────────────────────────────────────


class TestHistoryPage:
    def test_lists_recent_files(self, qapp, recent, tmp_path: Path):
        data = tmp_path / "data.csv"
        data.write_text("a\n1\n", encoding="utf-8")
        recent.add(data)

        page = HistoryPage(recent)
        assert page._files_layout.count() == 1
        assert page._files_empty.isHidden()

    def test_jobs_accumulate_newest_first(self, qapp, recent, report):
        page = HistoryPage(recent)
        page.add_job(report)
        page.add_job({**report, "status": "cancelled"})

        assert page._jobs_layout.count() == 2
        assert page._jobs[0]["status"] == "cancelled"

    def test_relative_time_handles_bad_input(self):
        assert _relative_time("not a timestamp") == ""


# ── Settings ────────────────────────────────────────────────────────


class TestSettingsPage:
    def test_theme_chips_are_mutually_exclusive(self, qapp):
        from deskx.gui.theme import ThemeMode

        page = SettingsPage()
        page.set_theme_mode(ThemeMode.DARK)
        assert page._dark_chip.isChecked()
        assert not page._light_chip.isChecked()

    def test_missing_folder_is_not_saved(self, qapp, tmp_path: Path):
        page = SettingsPage()
        messages: list[str] = []
        page.notify.connect(messages.append)

        page._location_edit.setText(str(tmp_path / "nowhere"))
        page._save_location()

        assert messages and "doesn't exist" in messages[0]
