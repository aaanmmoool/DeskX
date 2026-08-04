"""Main application window — single-flow design.

Implements a streamlined two-screen workflow:
  Screen 1: Upload    → drag-and-drop or browse
  Screen 2: Configure → preview table + transforms + process button

No nav bar, no separate results page.  Output is always saved
to the same folder as the source file.
"""

from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from PySide6.QtGui import QKeySequence, QShortcut

from deskx.core.config import APP_DISPLAY_NAME, SANITIZED_SUFFIX
from deskx.core.utils import build_output_filename
from deskx.gui.pages.upload_page import UploadPage
from deskx.gui.pages.configure_page import ConfigurePage
from deskx.gui.theme.colors import ThemeMode
from deskx.gui.theme.stylesheet import generate_stylesheet
from deskx.gui.widgets.help_dialog import HelpDialog
from deskx.gui.widgets.welcome_dialog import WelcomeDialog
from deskx.history.recent_files import RecentFilesManager
from deskx.processing.job import JobConfig
from deskx.processing.pipeline import TransformStep
from deskx.services.background_worker import BackgroundWorker
from deskx.services.progress import CompletionEvent, ErrorEvent, ProgressEvent



class MainWindow(QMainWindow):
    """Root application window — single-flow design."""

    def __init__(self) -> None:
        super().__init__()
        self._theme_mode = ThemeMode.DARK
        self._recent = RecentFilesManager()
        self._source_path: Path | None = None
        self._worker: BackgroundWorker | None = None

        self.setWindowTitle(APP_DISPLAY_NAME)
        self.setMinimumSize(1080, 700)
        self.resize(1320, 840)

        self._setup_ui()
        self._connect_signals()
        self._apply_theme()

        if WelcomeDialog.should_show():
            QTimer.singleShot(150, self._show_welcome_dialog)


    # ── Setup ───────────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Top bar ─────────────────────────────────────────────────
        self._top_bar = QFrame()
        self._top_bar.setObjectName("topBar")
        self._top_bar.setFixedHeight(52)
        top_layout = QHBoxLayout(self._top_bar)
        top_layout.setContentsMargins(20, 0, 20, 0)
        top_layout.setSpacing(12)

        # App title
        app_title = QLabel(f"✦  {APP_DISPLAY_NAME}")
        app_title.setStyleSheet("font-size: 15px; font-weight: 600;")
        top_layout.addWidget(app_title)

        top_layout.addStretch()

        # Help button
        self._help_btn = QPushButton("❓  Help")
        self._help_btn.setProperty("role", "ghost")
        self._help_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._help_btn.setFixedHeight(32)
        top_layout.addWidget(self._help_btn)

        # Theme toggle
        self._theme_btn = QPushButton("🌙  Dark")
        self._theme_btn.setProperty("role", "ghost")
        self._theme_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._theme_btn.setFixedHeight(32)
        top_layout.addWidget(self._theme_btn)

        root.addWidget(self._top_bar)

        # ── Stacked screens ─────────────────────────────────────────
        self._stack = QStackedWidget()
        self._upload_page = UploadPage(self._recent)
        self._configure_page = ConfigurePage()

        self._stack.addWidget(self._upload_page)
        self._stack.addWidget(self._configure_page)

        root.addWidget(self._stack, stretch=1)

        # ── Bottom status bar ───────────────────────────────────────
        self._status_bar = QFrame()
        self._status_bar.setObjectName("statusBar")
        self._status_bar.setFixedHeight(40)
        status_layout = QHBoxLayout(self._status_bar)
        status_layout.setContentsMargins(20, 0, 20, 0)
        status_layout.setSpacing(12)

        self._status_label = QLabel("Ready")
        self._status_label.setProperty("role", "caption")
        status_layout.addWidget(self._status_label)

        status_layout.addStretch()

        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        self._progress.setTextVisible(False)
        self._progress.setFixedWidth(200)
        self._progress.setFixedHeight(8)
        self._progress.setVisible(False)
        status_layout.addWidget(self._progress)

        root.addWidget(self._status_bar)

    def _connect_signals(self) -> None:
        # Theme
        self._theme_btn.clicked.connect(self._toggle_theme)

        # Help button & F1 shortcut
        self._help_btn.clicked.connect(self._show_help_dialog)
        QShortcut(QKeySequence("F1"), self, self._show_help_dialog)

        # File selected → go to configure
        self._upload_page.file_selected.connect(self._on_file_selected)

        # Back to upload
        self._configure_page.back_requested.connect(self._go_to_upload)

        # Process requested
        self._configure_page.process_requested.connect(self._on_process)


    # ── Slots ───────────────────────────────────────────────────────

    def _on_file_selected(self, path: str) -> None:
        """File chosen → load into configure page and switch."""
        self._source_path = Path(path)
        self._configure_page.load_file(path)
        self._stack.setCurrentIndex(1)
        self._status_label.setText(f"Loaded: {self._source_path.name}")

    def _show_welcome_dialog(self) -> None:
        """Show onboarding dialog on first run."""
        dlg = WelcomeDialog(self)
        dlg.exec()
        if dlg.load_sample_requested:
            self._upload_page._on_load_sample()

    def _show_help_dialog(self) -> None:
        """Open built-in user guide modal."""
        dlg = HelpDialog(self)
        dlg.exec()

    def _go_to_upload(self) -> None:
        """Back button → return to upload screen."""
        self._stack.setCurrentIndex(0)
        self._source_path = None
        self._status_label.setText("Ready")


    def _on_process(self) -> None:
        """Process button clicked → run pipeline."""
        if not self._source_path:
            return

        # Output to same folder
        output_name = build_output_filename(
            self._source_path, SANITIZED_SUFFIX
        )
        output_path = self._source_path.parent / output_name

        # Gather config from configure page
        import_settings = self._configure_page.get_import_settings()
        selected_columns = self._configure_page.get_selected_columns()
        transform_steps = self._configure_page.get_transform_steps()

        config = JobConfig(
            source_path=self._source_path,
            output_path=output_path,
            selected_columns=selected_columns,
            transform_steps=transform_steps,
            header_row=import_settings.get("header_row", 0),
            sheet_name=import_settings.get("sheet_name", 0),
            delimiter=import_settings.get("delimiter"),
        )

        # Update UI state
        self._configure_page.set_processing(True)
        self._progress.setVisible(True)
        self._progress.setValue(0)
        self._status_label.setText("Processing…")

        # Launch worker
        self._worker = BackgroundWorker(config)
        self._worker.progress.connect(self._on_progress)
        self._worker.completed.connect(self._on_completed)
        self._worker.failed.connect(self._on_failed)
        self._worker.start()

    def _on_progress(self, event: ProgressEvent) -> None:
        self._progress.setValue(event.percent)
        self._status_label.setText(event.message)

    def _on_completed(self, event: CompletionEvent) -> None:
        self._configure_page.set_processing(False)
        self._progress.setValue(100)

        # Parse report for output path
        try:
            report = json.loads(event.report_json)
            output_path = report.get("output_path", "")
            row_count = report.get("row_count")
            source_hash = report.get("source_hash", "")[:12]
            output_hash = report.get("output_hash", "")[:12]
        except (json.JSONDecodeError, KeyError):
            output_path = ""
            row_count = None
            source_hash = ""
            output_hash = ""

        # Show success on configure page
        self._configure_page.show_success(output_path, row_count)
        self._status_label.setText(f"✅  Saved to {Path(output_path).name}")

        # Hide progress after a moment
        QTimer.singleShot(3000, lambda: self._progress.setVisible(False))

    def _on_failed(self, event: ErrorEvent) -> None:
        self._configure_page.set_processing(False)
        self._progress.setVisible(False)
        self._progress.setValue(0)
        icon = "⚠️" if event.is_cancellation else "❌"
        self._status_label.setText(f"{icon}  {event.message}")
        self._configure_page.show_error(event.message)

    # ── Theming ─────────────────────────────────────────────────────

    def _toggle_theme(self) -> None:
        self._theme_mode = (
            ThemeMode.LIGHT
            if self._theme_mode is ThemeMode.DARK
            else ThemeMode.DARK
        )
        self._apply_theme()

    def _apply_theme(self) -> None:
        qss = generate_stylesheet(self._theme_mode)
        app = QApplication.instance()
        if app:
            app.setStyleSheet(qss)

        is_dark = self._theme_mode is ThemeMode.DARK
        self._theme_btn.setText("🌙  Dark" if is_dark else "☀️  Light")
