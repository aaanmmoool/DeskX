"""Configure & Preview screen — the main workspace.

Replaces the old separate Preview + Results pages with a single
unified screen that shows:

  ┌────────────────────────────────────────────────────────┐
  │ ← Back    file_name.csv (size)     ▶ Process & Save   │
  ├────────────────────────┬───────────────────────────────┤
  │                        │  Import Settings              │
  │    Data Preview Table  │  Column Selector              │
  │                        │  Transforms Pipeline          │
  │                        │  Sensitive Data Alerts         │
  │                        │                               │
  └────────────────────────┴───────────────────────────────┘
  │ Success / Error banner (appears after processing)      │
  └────────────────────────────────────────────────────────┘
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from deskx.adapters.adapter_registry import create_default_registry
from deskx.core.config import MAX_PREVIEW_ROWS
from deskx.core.utils import humanize_bytes
from deskx.gui.widgets.file_table import DataFrameModel, FileTableView
from deskx.gui.widgets.transform_sidebar import TransformSidebar
from deskx.processing.pipeline import TransformStep
from deskx.processing.sensitive_detector import (
    SensitiveColumn,
    detect_sensitive_columns,
)

logger = logging.getLogger(__name__)

_DELIMITERS = [
    ("Tab (\\t)", "\t"),
    ("Comma (,)", ","),
    ("Semicolon (;)", ";"),
    ("Pipe (|)", "|"),
    ("Space", " "),
]


class ConfigurePage(QWidget):
    """Preview + configure + process — all on one screen.

    Signals
    -------
    back_requested()
        Emitted when the user clicks the back button.
    process_requested()
        Emitted when the user clicks Process & Save.
    """

    back_requested = Signal()
    process_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._registry = create_default_registry()
        self._df: pd.DataFrame | None = None
        self._source_path: Path | None = None
        self._checkboxes: list[QCheckBox] = []
        self._sensitive_results: list[SensitiveColumn] = []
        self._current_page: int = 0
        self._setup_ui()

    # ── Public API ──────────────────────────────────────────────────

    def load_file(self, path: str) -> None:
        """Load a file and populate all UI elements."""
        file_path = Path(path)
        self._source_path = file_path

        # Update file info in toolbar
        self._file_label.setText(f"  {file_path.name}")
        try:
            size = humanize_bytes(file_path.stat().st_size)
            self._size_label.setText(size)
        except OSError:
            self._size_label.setText("")

        # Show/hide format-specific controls
        ext = file_path.suffix.lower()
        self._sheet_row.setVisible(ext == ".xlsx")
        self._delim_row.setVisible(ext == ".txt")

        # Load sheet names for XLSX
        if ext == ".xlsx":
            try:
                adapter = self._registry.get(ext)
                sheets = adapter.get_sheet_names(file_path)
                self._sheet_combo.blockSignals(True)
                self._sheet_combo.clear()
                self._sheet_combo.addItems(sheets)
                self._sheet_combo.blockSignals(False)
            except Exception:
                logger.exception("Failed to read sheet names")

        # Auto-detect delimiter for TXT
        if ext == ".txt":
            try:
                adapter = self._registry.get(ext)
                detected = adapter.detect_delimiter(file_path)
                if detected:
                    for i, (_, delim) in enumerate(_DELIMITERS):
                        if delim == detected:
                            self._delim_combo.blockSignals(True)
                            self._delim_combo.setCurrentIndex(i)
                            self._delim_combo.blockSignals(False)
                            break
            except Exception:
                logger.exception("Failed to detect delimiter")

        # Hide success/error banners
        self._success_banner.setVisible(False)
        self._error_banner.setVisible(False)

        self._reload_preview()

    def get_import_settings(self) -> dict:
        """Return current import settings."""
        settings = {}
        settings["header_row"] = self._get_header_row()

        if self._source_path and self._source_path.suffix.lower() == ".xlsx":
            settings["sheet_name"] = self._sheet_combo.currentText()

        if self._source_path and self._source_path.suffix.lower() == ".txt":
            idx = self._delim_combo.currentIndex()
            if 0 <= idx < len(_DELIMITERS):
                settings["delimiter"] = _DELIMITERS[idx][1]

        return settings

    def get_selected_columns(self) -> list[str]:
        """Return the list of currently selected column names."""
        return [
            cb.property("col_name")
            for cb in self._checkboxes
            if cb.isChecked()
        ]

    def get_transform_steps(self) -> list[TransformStep]:
        """Return the configured transform pipeline."""
        return self._transform_sidebar.get_pipeline()

    def set_processing(self, running: bool) -> None:
        """Toggle UI state during processing."""
        self._process_btn.setEnabled(not running)
        self._process_btn.setText(
            "⏳  Processing…" if running else "▶  Process & Save"
        )
        self._back_btn.setEnabled(not running)

    def show_success(self, output_path: str, row_count: int | None) -> None:
        """Show success banner after processing completes."""
        name = Path(output_path).name
        msg = f"✅  Saved as  {name}"
        if row_count is not None:
            msg += f"   ({row_count:,} rows)"
        self._success_msg.setText(msg)
        self._success_banner.setVisible(True)
        self._error_banner.setVisible(False)

    def show_error(self, message: str) -> None:
        """Show error banner."""
        self._error_msg.setText(f"  {message}")
        self._error_banner.setVisible(True)
        self._success_banner.setVisible(False)

    # ── Setup ───────────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ═══ Toolbar ════════════════════════════════════════════════
        toolbar = QFrame()
        toolbar.setObjectName("configToolbar")
        toolbar.setFixedHeight(50)
        tb_layout = QHBoxLayout(toolbar)
        tb_layout.setContentsMargins(16, 0, 16, 0)
        tb_layout.setSpacing(12)

        # Back button
        self._back_btn = QPushButton("←  Back")
        self._back_btn.setProperty("role", "ghost")
        self._back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._back_btn.setFixedHeight(34)
        self._back_btn.clicked.connect(self.back_requested.emit)
        tb_layout.addWidget(self._back_btn)

        # File name + size
        self._file_label = QLabel("  file.csv")
        self._file_label.setStyleSheet("font-weight: 600; font-size: 14px;")
        tb_layout.addWidget(self._file_label)

        self._size_label = QLabel("")
        self._size_label.setProperty("role", "caption")
        tb_layout.addWidget(self._size_label)

        self._stats_label = QLabel("")
        self._stats_label.setProperty("role", "caption")
        tb_layout.addWidget(self._stats_label)

        tb_layout.addStretch()

        # Process button
        self._process_btn = QPushButton("▶  Process & Save")
        self._process_btn.setProperty("role", "primary")
        self._process_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._process_btn.setFixedHeight(38)
        self._process_btn.setMinimumWidth(180)
        self._process_btn.clicked.connect(self.process_requested.emit)
        tb_layout.addWidget(self._process_btn)

        root.addWidget(toolbar)

        # Separator
        sep = QFrame()
        sep.setProperty("role", "separator")
        sep.setFrameShape(QFrame.Shape.HLine)
        root.addWidget(sep)

        # ═══ Main content ═══════════════════════════════════════════
        content = QHBoxLayout()
        content.setContentsMargins(0, 0, 0, 0)
        content.setSpacing(0)

        # ── Left: Preview table ─────────────────────────────────────
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(16, 12, 8, 12)
        left_layout.setSpacing(8)

        # Search Bar
        top_bar = QHBoxLayout()
        top_bar.setSpacing(6)
        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText(
            "🔍 Search rows by text across all columns..."
        )
        self._search_edit.setClearButtonEnabled(True)
        self._search_edit.textChanged.connect(
            lambda: self._update_table_view(reset_page=True)
        )
        top_bar.addWidget(self._search_edit)
        left_layout.addLayout(top_bar)

        self._model = DataFrameModel()
        self._table = FileTableView()
        self._table.setModel(self._model)
        left_layout.addWidget(self._table, stretch=1)

        # Pagination Toolbar
        bot_bar = QHBoxLayout()
        bot_bar.setSpacing(8)
        lbl = QLabel("Rows per page:")
        lbl.setProperty("role", "caption")
        bot_bar.addWidget(lbl)
        self._page_size_combo = QComboBox()
        self._page_size_combo.addItems(["25", "50", "100", "500"])
        self._page_size_combo.setCurrentText("50")
        self._page_size_combo.setFixedWidth(70)
        self._page_size_combo.currentTextChanged.connect(
            lambda: self._update_table_view(reset_page=True)
        )
        bot_bar.addWidget(self._page_size_combo)
        bot_bar.addStretch()

        self._prev_page_btn = QPushButton("← Prev")
        self._prev_page_btn.setProperty("role", "ghost")
        self._prev_page_btn.clicked.connect(self._on_prev_page)
        bot_bar.addWidget(self._prev_page_btn)

        self._page_label = QLabel("Page 1 of 1")
        self._page_label.setProperty("role", "caption")
        bot_bar.addWidget(self._page_label)

        self._next_page_btn = QPushButton("Next →")
        self._next_page_btn.setProperty("role", "ghost")
        self._next_page_btn.clicked.connect(self._on_next_page)
        bot_bar.addWidget(self._next_page_btn)
        left_layout.addLayout(bot_bar)

        content.addWidget(left, stretch=3)

        # ── Right: Settings sidebar ─────────────────────────────────
        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setFrameShape(QFrame.Shape.NoFrame)
        right_scroll.setFixedWidth(320)
        right_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(8, 12, 16, 12)
        right_layout.setSpacing(12)

        # ── Import settings ─────────────────────────────────────────
        import_card = QFrame()
        import_card.setProperty("role", "card")
        import_layout = QVBoxLayout(import_card)
        import_layout.setContentsMargins(14, 12, 14, 12)
        import_layout.setSpacing(8)

        import_title = QLabel("Import Settings")
        import_title.setStyleSheet("font-weight: 600; font-size: 13px;")
        import_layout.addWidget(import_title)

        # Header row
        header_row_widget = QHBoxLayout()
        header_row_widget.setSpacing(6)
        hl = QLabel("Header:")
        hl.setProperty("role", "caption")
        hl.setFixedWidth(50)
        header_row_widget.addWidget(hl)

        self._header_group = QButtonGroup(self)
        self._header_first = QRadioButton("Row 1 (Standard)")
        self._header_first.setChecked(True)
        self._header_first.setToolTip("Use the first row as column titles")
        self._header_specific = QRadioButton("Row #:")
        self._header_specific.setToolTip("Use a specific row number as column titles")
        self._header_none = QRadioButton("No Header")
        self._header_none.setToolTip("Do not use any row as headers; auto-name columns 0, 1, 2...")
        self._header_group.addButton(self._header_first, 0)
        self._header_group.addButton(self._header_specific, 1)
        self._header_group.addButton(self._header_none, 2)

        self._header_spin = QSpinBox()
        self._header_spin.setMinimum(1)
        self._header_spin.setMaximum(100)
        self._header_spin.setValue(1)
        self._header_spin.setFixedWidth(52)
        self._header_spin.setEnabled(False)

        header_row_widget.addWidget(self._header_first)
        header_row_widget.addWidget(self._header_specific)
        header_row_widget.addWidget(self._header_spin)
        header_row_widget.addWidget(self._header_none)
        header_row_widget.addStretch()
        import_layout.addLayout(header_row_widget)

        # Sheet selector (XLSX)
        self._sheet_row = QWidget()
        sr_layout = QHBoxLayout(self._sheet_row)
        sr_layout.setContentsMargins(0, 0, 0, 0)
        sr_layout.setSpacing(6)
        sl = QLabel("Sheet:")
        sl.setProperty("role", "caption")
        sl.setFixedWidth(50)
        sr_layout.addWidget(sl)
        self._sheet_combo = QComboBox()
        sr_layout.addWidget(self._sheet_combo)
        self._sheet_row.setVisible(False)
        import_layout.addWidget(self._sheet_row)

        # Delimiter selector (TXT)
        self._delim_row = QWidget()
        dr_layout = QHBoxLayout(self._delim_row)
        dr_layout.setContentsMargins(0, 0, 0, 0)
        dr_layout.setSpacing(6)
        dl = QLabel("Delim:")
        dl.setProperty("role", "caption")
        dl.setFixedWidth(50)
        dr_layout.addWidget(dl)
        self._delim_combo = QComboBox()
        for label, _ in _DELIMITERS:
            self._delim_combo.addItem(label)
        dr_layout.addWidget(self._delim_combo)
        self._delim_row.setVisible(False)
        import_layout.addWidget(self._delim_row)

        right_layout.addWidget(import_card)

        # Connect import setting changes
        self._header_group.buttonClicked.connect(self._on_settings_changed)
        self._header_spin.valueChanged.connect(self._on_settings_changed)
        self._sheet_combo.currentIndexChanged.connect(self._on_settings_changed)
        self._delim_combo.currentIndexChanged.connect(self._on_settings_changed)

        # ── Column selector ─────────────────────────────────────────
        col_card = QFrame()
        col_card.setProperty("role", "card")
        col_layout = QVBoxLayout(col_card)
        col_layout.setContentsMargins(14, 12, 14, 12)
        col_layout.setSpacing(6)

        col_header = QHBoxLayout()
        col_title = QLabel("Columns")
        col_title.setStyleSheet("font-weight: 600; font-size: 13px;")
        col_header.addWidget(col_title)

        self._col_count_label = QLabel("")
        self._col_count_label.setProperty("role", "caption")
        col_header.addStretch()
        col_header.addWidget(self._col_count_label)
        col_layout.addLayout(col_header)

        # Select all
        self._select_all_cb = QCheckBox("Select All")
        self._select_all_cb.setChecked(True)
        self._select_all_cb.stateChanged.connect(self._on_select_all)
        col_layout.addWidget(self._select_all_cb)

        # Column checkboxes (scrollable)
        self._cb_container = QWidget()
        self._cb_layout = QVBoxLayout(self._cb_container)
        self._cb_layout.setContentsMargins(0, 0, 0, 0)
        self._cb_layout.setSpacing(1)
        self._cb_layout.addStretch()

        cb_scroll = QScrollArea()
        cb_scroll.setWidgetResizable(True)
        cb_scroll.setFrameShape(QFrame.Shape.NoFrame)
        cb_scroll.setMaximumHeight(200)
        cb_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        cb_scroll.setWidget(self._cb_container)
        col_layout.addWidget(cb_scroll)

        # Sensitive data alerts
        self._sensitive_frame = QFrame()
        sens_layout = QVBoxLayout(self._sensitive_frame)
        sens_layout.setContentsMargins(0, 6, 0, 0)
        sens_layout.setSpacing(4)
        sens_title = QLabel("⚠  Sensitive data detected")
        sens_title.setStyleSheet("color: #FBBF24; font-weight: 600; font-size: 11px;")
        sens_layout.addWidget(sens_title)
        self._sensitive_list = QLabel("")
        self._sensitive_list.setProperty("role", "caption")
        self._sensitive_list.setWordWrap(True)
        sens_layout.addWidget(self._sensitive_list)
        self._sensitive_frame.setVisible(False)
        col_layout.addWidget(self._sensitive_frame)

        right_layout.addWidget(col_card)

        # ── Transform sidebar ───────────────────────────────────────
        self._transform_sidebar = TransformSidebar()
        self._transform_sidebar.setFixedWidth(290)
        right_layout.addWidget(self._transform_sidebar)

        right_layout.addStretch()

        right_scroll.setWidget(right)
        content.addWidget(right_scroll)

        root.addLayout(content, stretch=1)

        # ═══ Success / Error banners ════════════════════════════════
        self._success_banner = QFrame()
        self._success_banner.setObjectName("successBanner")
        self._success_banner.setFixedHeight(48)
        sb_layout = QHBoxLayout(self._success_banner)
        sb_layout.setContentsMargins(20, 0, 20, 0)
        self._success_msg = QLabel("")
        self._success_msg.setStyleSheet("font-weight: 600; font-size: 13px;")
        sb_layout.addWidget(self._success_msg)
        sb_layout.addStretch()
        self._success_banner.setVisible(False)
        root.addWidget(self._success_banner)

        self._error_banner = QFrame()
        self._error_banner.setObjectName("errorBanner")
        self._error_banner.setFixedHeight(48)
        eb_layout = QHBoxLayout(self._error_banner)
        eb_layout.setContentsMargins(20, 0, 20, 0)
        self._error_msg = QLabel("")
        self._error_msg.setStyleSheet("font-weight: 600; font-size: 13px;")
        eb_layout.addWidget(self._error_msg)
        eb_layout.addStretch()
        self._error_banner.setVisible(False)
        root.addWidget(self._error_banner)

    # ── Internal ────────────────────────────────────────────────────

    def _get_header_row(self) -> int | None:
        checked_id = self._header_group.checkedId()
        if checked_id == 0:
            return 0
        elif checked_id == 1:
            return self._header_spin.value() - 1
        else:
            return None

    def _on_settings_changed(self, *_args) -> None:
        self._header_spin.setEnabled(self._header_group.checkedId() == 1)
        if self._source_path:
            self._reload_preview()

    def _reload_preview(self) -> None:
        if not self._source_path:
            return

        try:
            adapter = self._registry.get(self._source_path.suffix)
            kwargs = self.get_import_settings()
            df = adapter.read_preview(
                self._source_path, MAX_PREVIEW_ROWS, **kwargs
            )
        except Exception as exc:
            logger.exception("Failed to load preview")
            QMessageBox.warning(
                self, "Load Error", f"Could not load file:\n\n{exc}"
            )
            return

        self._df = df
        self._transform_sidebar.set_sample_data(df)
        self._update_table_view(reset_page=True)
        self._update_stats(df)
        self._build_column_checkboxes(df)
        self._run_sensitive_detection(df)

    def _on_prev_page(self) -> None:
        self._current_page = max(0, self._current_page - 1)
        self._update_table_view(reset_page=False)

    def _on_next_page(self) -> None:
        self._current_page += 1
        self._update_table_view(reset_page=False)

    def _update_table_view(self, reset_page: bool = True) -> None:
        if self._df.empty:
            self._model.update_dataframe(self._df)
            self._page_label.setText("Page 1 of 1")
            self._prev_page_btn.setEnabled(False)
            self._next_page_btn.setEnabled(False)
            return

        query = self._search_edit.text().strip().lower()
        if query:
            mask = self._df.astype(str).apply(
                lambda row: row.str.lower().str.contains(query, regex=False).any(),
                axis=1,
            )
            filtered_df = self._df[mask]
        else:
            filtered_df = self._df

        page_size = int(self._page_size_combo.currentText())
        total_pages = max(1, (len(filtered_df) + page_size - 1) // page_size)
        if reset_page or self._current_page >= total_pages:
            self._current_page = 0

        start_idx = self._current_page * page_size
        end_idx = start_idx + page_size
        page_df = filtered_df.iloc[start_idx:end_idx]
        self._model.update_dataframe(page_df)

        self._page_label.setText(
            f"Page {self._current_page + 1} of {total_pages} ({len(filtered_df):,} rows)"
        )
        self._prev_page_btn.setEnabled(self._current_page > 0)
        self._next_page_btn.setEnabled(self._current_page < total_pages - 1)

    def _update_stats(self, df: pd.DataFrame) -> None:
        rows = len(df)
        cols = len(df.columns)
        self._stats_label.setText(
            f"  {rows:,} rows  ×  {cols} columns"
        )

    def _build_column_checkboxes(self, df: pd.DataFrame) -> None:
        for cb in self._checkboxes:
            self._cb_layout.removeWidget(cb)
            cb.deleteLater()
        self._checkboxes.clear()

        for i, col in enumerate(df.columns):
            dtype = str(df[col].dtype)
            missing = df[col].isna().sum()
            label = col
            if missing > 0:
                label += f"  ({missing} missing)"

            cb = QCheckBox(label)
            cb.setChecked(True)
            cb.setProperty("col_name", col)
            cb.setToolTip(
                f"Type: {dtype}\n"
                f"Missing: {missing}/{len(df)}\n"
                f"Unique: {df[col].nunique()}"
            )
            cb.stateChanged.connect(self._on_column_toggled)
            self._cb_layout.insertWidget(
                self._cb_layout.count() - 1, cb
            )
            self._checkboxes.append(cb)

        self._select_all_cb.setChecked(True)
        self._col_count_label.setText(f"{len(df.columns)} total")

        # Update sidebar columns
        self._transform_sidebar.set_columns(list(df.columns))

    def _run_sensitive_detection(self, df: pd.DataFrame) -> None:
        self._sensitive_results = detect_sensitive_columns(df)

        if self._sensitive_results:
            lines = []
            for sc in self._sensitive_results[:6]:
                conf = f"{sc.confidence:.0%}"
                lines.append(f"• {sc.column_name} → {sc.category} ({conf})")
            self._sensitive_list.setText("\n".join(lines))
            self._sensitive_frame.setVisible(True)

            # Push to transform sidebar
            self._transform_sidebar.set_sensitive_columns(
                self._sensitive_results
            )
        else:
            self._sensitive_frame.setVisible(False)

    def _on_select_all(self, state: int) -> None:
        checked = state == Qt.CheckState.Checked.value
        for cb in self._checkboxes:
            cb.blockSignals(True)
            cb.setChecked(checked)
            cb.blockSignals(False)

    def _on_column_toggled(self) -> None:
        all_checked = all(cb.isChecked() for cb in self._checkboxes)
        self._select_all_cb.blockSignals(True)
        self._select_all_cb.setChecked(all_checked)
        self._select_all_cb.blockSignals(False)

        selected = sum(1 for cb in self._checkboxes if cb.isChecked())
        total = len(self._checkboxes)
        self._col_count_label.setText(
            f"{selected}/{total}" if selected < total else f"{total} total"
        )

    @property
    def sensitive_columns(self) -> list[SensitiveColumn]:
        return list(self._sensitive_results)
