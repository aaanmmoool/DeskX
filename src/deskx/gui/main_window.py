"""Application shell.

A persistent navigation rail on the left, one screen at a time on the
right, and a slim status strip along the bottom.  The window owns the
theme, routes navigation, and drives the workflow:

    Upload → Preview → Configure → Review → Save location → Process → Results

The processing engine is untouched.  ``MainWindow`` only decides *when*
to build a :class:`JobConfig` and *where* the output goes — the answer
to "where" now comes from :class:`SaveDestinationDialog` instead of
being assumed.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFrame,
    QHBoxLayout,
    QMainWindow,
    QProgressBar,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from deskx.core.config import APP_DISPLAY_NAME
from deskx.gui.pages.configure_page import ConfigurePage
from deskx.gui.pages.history_page import HistoryPage
from deskx.gui.pages.home_page import HomePage
from deskx.gui.pages.processing_page import ProcessingPage
from deskx.gui.pages.reports_page import ReportsPage
from deskx.gui.pages.results_page import ResultsPage
from deskx.gui.pages.settings_page import SettingsPage
from deskx.gui.pages.upload_page import UploadPage
from deskx.gui.theme import SPACE, ThemeMode, palette, set_mode
from deskx.gui.theme.colors import ColorPalette
from deskx.gui.theme.icons import Icon, get_pixmap, icon_label
from deskx.gui.theme.stylesheet import generate_stylesheet
from deskx.gui.widgets.components import Themed, label
from deskx.gui.widgets.help_dialog import HelpDialog, PrivacyDialog
from deskx.gui.widgets.save_destination_dialog import SaveDestinationDialog
from deskx.gui.widgets.sidebar_nav import SidebarNav
from deskx.gui.widgets.toast import show_toast
from deskx.gui.widgets.welcome_dialog import WelcomeDialog
from deskx.history.recent_files import RecentFilesManager
from deskx.history.saved_pipeline import save_pipeline
from deskx.processing.job import JobConfig
from deskx.processing.pipeline import TransformStep
from deskx.services.background_worker import BackgroundWorker
from deskx.services.progress import CompletionEvent, ErrorEvent, ProgressEvent

logger = logging.getLogger(__name__)

# Screen order inside the stack.
PAGE_HOME = 0
PAGE_UPLOAD = 1
PAGE_CONFIGURE = 2
PAGE_PROCESSING = 3
PAGE_RESULTS = 4
PAGE_HISTORY = 5
PAGE_REPORTS = 6
PAGE_SETTINGS = 7

# Which navigation entry lights up for each screen.
_NAV_FOR_PAGE = {
    PAGE_HOME: "home",
    PAGE_UPLOAD: "files",
    PAGE_CONFIGURE: "transform",
    PAGE_PROCESSING: "transform",
    PAGE_RESULTS: "transform",
    PAGE_HISTORY: "history",
    PAGE_REPORTS: "reports",
    PAGE_SETTINGS: "settings",
}

_PAGE_FOR_NAV = {
    "home": PAGE_HOME,
    "files": PAGE_UPLOAD,
    "transform": PAGE_CONFIGURE,
    "history": PAGE_HISTORY,
    "reports": PAGE_REPORTS,
    "settings": PAGE_SETTINGS,
}


class MainWindow(QMainWindow, Themed):
    """Root application window."""

    def __init__(self) -> None:
        super().__init__()
        self._theme_mode = ThemeMode.LIGHT
        self._recent = RecentFilesManager()
        self._source_path: Path | None = None
        self._output_path: Path | None = None
        self._worker: BackgroundWorker | None = None
        self._last_report: dict = {}
        self._save_pipeline_after_success = False
        self._pipeline_steps_for_save: list[TransformStep] = []

        self.setWindowTitle(APP_DISPLAY_NAME)
        self.setMinimumSize(1100, 700)
        self.resize(1360, 860)

        self._setup_ui()
        self._connect_signals()
        self._install_shortcuts()
        self._apply_theme()
        self._register_theme()

        if WelcomeDialog.should_show():
            QTimer.singleShot(150, self._show_welcome_dialog)

    # ── Setup ───────────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)

        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._sidebar = SidebarNav()
        root.addWidget(self._sidebar)

        right = QWidget()
        right.setObjectName("pageRoot")
        right_col = QVBoxLayout(right)
        right_col.setContentsMargins(0, 0, 0, 0)
        right_col.setSpacing(0)

        self._stack = QStackedWidget()
        self._home_page = HomePage(self._recent)
        self._upload_page = UploadPage(self._recent)
        self._configure_page = ConfigurePage()
        self._processing_page = ProcessingPage()
        self._results_page = ResultsPage()
        self._history_page = HistoryPage(self._recent)
        self._reports_page = ReportsPage()
        self._settings_page = SettingsPage()

        for page in (
            self._home_page,
            self._upload_page,
            self._configure_page,
            self._processing_page,
            self._results_page,
            self._history_page,
            self._reports_page,
            self._settings_page,
        ):
            self._stack.addWidget(page)

        right_col.addWidget(self._stack, 1)
        right_col.addWidget(self._build_status_strip())
        root.addWidget(right, 1)

        self._sidebar.set_enabled_item("transform", False)

    def _build_status_strip(self) -> QWidget:
        bar = QFrame()
        bar.setObjectName("statusBar")
        bar.setFixedHeight(38)

        row = QHBoxLayout(bar)
        row.setContentsMargins(SPACE.xl, 0, SPACE.xl, 0)
        row.setSpacing(SPACE.sm)

        self._status_icon = icon_label(Icon.LOCK, palette().success, 14)
        row.addWidget(self._status_icon)

        self._status_label = label("Ready — everything runs on this device", "caption")
        row.addWidget(self._status_label)

        row.addStretch()

        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        self._progress.setTextVisible(False)
        self._progress.setFixedWidth(180)
        self._progress.setVisible(False)
        row.addWidget(self._progress)

        return bar

    def _connect_signals(self) -> None:
        self._sidebar.navigated.connect(self._on_navigate)

        self._home_page.open_file_requested.connect(
            lambda: self._go_to(PAGE_UPLOAD)
        )
        self._home_page.open_sample_requested.connect(
            self._upload_page._on_load_sample
        )
        self._home_page.file_selected.connect(self._on_file_selected)
        self._home_page.view_history_requested.connect(
            lambda: self._go_to(PAGE_HISTORY)
        )

        self._upload_page.file_selected.connect(self._on_file_selected)
        self._history_page.file_selected.connect(self._on_file_selected)

        self._configure_page.back_requested.connect(
            lambda: self._go_to(PAGE_UPLOAD)
        )
        self._configure_page.process_requested.connect(self._on_process)

        self._processing_page.cancel_requested.connect(self._on_cancel)

        self._results_page.open_report_requested.connect(
            lambda: self._go_to(PAGE_REPORTS)
        )
        self._results_page.process_another_requested.connect(self._start_over)

        self._reports_page.copied.connect(
            lambda message: show_toast(self, message, "success")
        )

        self._settings_page.theme_changed.connect(self._set_theme)
        self._settings_page.notify.connect(
            lambda message: show_toast(self, message, "info")
        )

    def _install_shortcuts(self) -> None:
        QShortcut(QKeySequence("F1"), self, self._show_help_dialog)
        QShortcut(
            QKeySequence.StandardKey.Open, self, self._upload_page._on_browse
        )

    # ── Navigation ──────────────────────────────────────────────────

    def _on_navigate(self, key: str) -> None:
        if key == "help":
            self._show_help_dialog()
            return
        if key == "privacy":
            PrivacyDialog(self).exec()
            return

        page = _PAGE_FOR_NAV.get(key)
        if page is None:
            return
        if page == PAGE_CONFIGURE and self._source_path is None:
            page = PAGE_UPLOAD
        self._go_to(page)

    def _go_to(self, page: int) -> None:
        """Switch screens and keep the rail in sync."""
        if page == PAGE_HOME:
            self._home_page.refresh(self._last_report or None)
        elif page == PAGE_HISTORY:
            self._history_page.refresh()
        elif page == PAGE_UPLOAD:
            self._upload_page.refresh()

        self._stack.setCurrentIndex(page)
        self._sidebar.set_current(_NAV_FOR_PAGE.get(page, "home"))

    # ── File selection ──────────────────────────────────────────────

    def _on_file_selected(self, path: str) -> None:
        """A dataset was chosen — load it and open the workspace."""
        file_path = Path(path)
        if not file_path.is_file():
            show_toast(self, "That file is no longer available", "error")
            return

        self._recent.add(file_path)
        self._source_path = file_path
        self._configure_page.load_file(str(file_path))
        self._sidebar.set_enabled_item("transform", True)
        self._go_to(PAGE_CONFIGURE)
        self._set_status(f"Loaded {file_path.name}", Icon.FILE, "primary")

    def _start_over(self) -> None:
        self._source_path = None
        self._output_path = None
        self._save_pipeline_after_success = False
        self._pipeline_steps_for_save = []
        self._sidebar.set_enabled_item("transform", False)
        self._go_to(PAGE_UPLOAD)
        self._set_status("Ready — everything runs on this device", Icon.LOCK, "success")

    # ── Processing ──────────────────────────────────────────────────

    def _on_process(self) -> None:
        """Ask where to save, then hand the job to the existing worker."""
        if self._source_path is None:
            return

        transform_steps = self._configure_page.get_transform_steps()
        dialog = SaveDestinationDialog(
            self._source_path,
            pipeline_step_count=len(transform_steps),
            parent=self,
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        destination = dialog.destination()
        if destination is None:
            show_toast(self, "That destination isn't usable — nothing was run", "error")
            return

        self._output_path = destination.output_path
        self._save_pipeline_after_success = destination.save_pipeline
        self._pipeline_steps_for_save = list(transform_steps)

        import_settings = self._configure_page.get_import_settings()

        config = JobConfig(
            source_path=self._source_path,
            output_path=destination.output_path,
            selected_columns=self._configure_page.get_selected_columns(),
            transform_steps=transform_steps,
            header_row=import_settings.get("header_row", 0),
            sheet_name=import_settings.get("sheet_name", 0),
            delimiter=import_settings.get("delimiter"),
        )

        self._configure_page.set_processing(True)
        self._processing_page.start(
            self._source_path, destination.output_path, len(transform_steps)
        )
        self._go_to(PAGE_PROCESSING)

        self._progress.setValue(0)
        self._progress.setVisible(True)
        self._set_status("Processing…", Icon.PROCESS, "primary")

        self._worker = BackgroundWorker(config)
        self._worker.progress.connect(self._on_progress)
        self._worker.completed.connect(self._on_completed)
        self._worker.failed.connect(self._on_failed)
        self._worker.start()

    def _on_cancel(self) -> None:
        if self._worker is not None and self._worker.isRunning():
            self._worker.cancel()
            self._processing_page.mark_cancelling()
            self._set_status("Cancelling…", Icon.WARNING, "warning")

    def _on_progress(self, event: ProgressEvent) -> None:
        self._progress.setValue(event.percent)
        self._processing_page.update_progress(event.percent, event.message)
        self._status_label.setText(event.message)

    def _on_completed(self, event: CompletionEvent) -> None:
        self._configure_page.set_processing(False)
        self._progress.setValue(100)

        report = _decode_report(event.report_json)
        self._last_report = report

        self._results_page.show_report(report)
        self._reports_page.set_report(report, event.report_json)
        self._history_page.add_job(report)
        self._home_page.refresh(report)

        pipeline_path: Path | None = None
        pipeline_error = False
        if self._save_pipeline_after_success and self._output_path is not None:
            try:
                pipeline_path = save_pipeline(
                    self._pipeline_steps_for_save, self._output_path
                )
            except (OSError, TypeError, ValueError):
                pipeline_error = True
                logger.exception("Could not save pipeline configuration.")
        self._save_pipeline_after_success = False
        self._pipeline_steps_for_save = []

        self._go_to(PAGE_RESULTS)

        name = Path(report.get("output_path", "")).name or "your file"
        self._set_status(f"Saved {name}", Icon.SUCCESS, "success")
        if pipeline_error:
            show_toast(
                self,
                f"Saved {name}, but the pipeline configuration could not be saved",
                "warning",
            )
        elif pipeline_path is not None:
            show_toast(
                self,
                f"Saved {name} and {pipeline_path.name}",
                "success",
            )
        else:
            show_toast(self, f"Saved {name}", "success")
        QTimer.singleShot(2500, lambda: self._progress.setVisible(False))

    def _on_failed(self, event: ErrorEvent) -> None:
        self._configure_page.set_processing(False)
        self._save_pipeline_after_success = False
        self._pipeline_steps_for_save = []
        self._progress.setVisible(False)
        self._progress.setValue(0)

        self._configure_page.show_error(event.message)
        self._go_to(PAGE_CONFIGURE)

        if event.is_cancellation:
            self._set_status("Processing cancelled", Icon.WARNING, "warning")
            show_toast(self, "Processing cancelled — no file was written", "warning")
        else:
            self._set_status(event.message, Icon.ERROR, "error")
            show_toast(self, "Processing failed. See the message above.", "error")

    # ── Dialogs ─────────────────────────────────────────────────────

    def _show_welcome_dialog(self) -> None:
        dialog = WelcomeDialog(self)
        dialog.exec()
        if dialog.load_sample_requested:
            self._upload_page._on_load_sample()

    def _show_help_dialog(self) -> None:
        HelpDialog(self).exec()

    # ── Status strip ────────────────────────────────────────────────

    def _set_status(self, message: str, icon: str, tone: str) -> None:
        self._status_label.setText(message)
        self._status_icon.setProperty("iconName", icon)
        self._status_tone = tone
        self._status_icon.setPixmap(
            get_pixmap(icon, getattr(palette(), tone, palette().text_secondary), 14)
        )

    # ── Theming ─────────────────────────────────────────────────────

    def _set_theme(self, new_mode: ThemeMode) -> None:
        self._theme_mode = new_mode
        self._apply_theme()

    def _apply_theme(self) -> None:
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(generate_stylesheet(self._theme_mode))
        # Notifies every Themed widget so cached icon pixmaps re-tint.
        set_mode(self._theme_mode)
        self._settings_page.set_theme_mode(self._theme_mode)

    def apply_theme(self, p: ColorPalette) -> None:
        tone = getattr(self, "_status_tone", "success")
        name = self._status_icon.property("iconName") or Icon.LOCK
        self._status_icon.setPixmap(
            get_pixmap(name, getattr(p, tone, p.text_secondary), 14)
        )

    # ── Qt overrides ────────────────────────────────────────────────

    def closeEvent(self, event) -> None:
        """Stop a running job before the window disappears."""
        worker = self._worker
        if worker is not None and worker.isRunning():
            worker.cancel()
            worker.wait(3000)
        super().closeEvent(event)


def _decode_report(report_json: str) -> dict:
    """Parse the worker's report, tolerating malformed JSON."""
    try:
        decoded = json.loads(report_json)
    except json.JSONDecodeError:
        logger.warning("Could not decode the job report.")
        return {}
    return decoded if isinstance(decoded, dict) else {}
