"""Step 2 — Preview & Configure Page.

Shows:
* Import settings: header row, worksheet (XLSX), delimiter (TXT)
* Data preview table (spreadsheet-like)
* Column metadata with data types, missing counts, sensitive flags
* Column checkboxes for selection
* File info bar (name, size, row count, column count)
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
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
from deskx.processing.sensitive_detector import (
    SensitiveColumn,
    detect_sensitive_columns,
)

logger = logging.getLogger(__name__)


# ── Delimiter options ──────────────────────────────────────────────
_DELIMITERS = [
    ("Tab (\\t)", "\t"),
    ("Comma (,)", ","),
    ("Semicolon (;)", ";"),
    ("Pipe (|)", "|"),
    ("Space", " "),
]


class PreviewPage(QWidget):
    """Data preview and column selection — Step 2.

    Signals
    -------
    columns_changed(list)
        Emitted whenever the column selection changes.
    """

    columns_changed = Signal(list)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._registry = create_default_registry()
        self._df: pd.DataFrame | None = None
        self._source_path: Path | None = None
        self._checkboxes: list[QCheckBox] = []
        self._sensitive_results: list[SensitiveColumn] = []
        self._setup_ui()

    # ── Public API ──────────────────────────────────────────────────

    def load_file(self, path: str) -> None:
        """Load a file preview from *path*."""
        file_path = Path(path)
        self._source_path = file_path

        # Show/hide format-specific controls
        ext = file_path.suffix.lower()
        self._sheet_section.setVisible(ext == ".xlsx")
        self._delimiter_section.setVisible(ext == ".txt")

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
                            self._delimiter_combo.blockSignals(True)
                            self._delimiter_combo.setCurrentIndex(i)
                            self._delimiter_combo.blockSignals(False)
                            break
            except Exception:
                logger.exception("Failed to detect delimiter")

        self._reload_preview()

    def get_import_settings(self) -> dict:
        """Return current import settings for use by the processing job."""
        settings = {}
        settings["header_row"] = self._get_header_row()

        if self._source_path and self._source_path.suffix.lower() == ".xlsx":
            settings["sheet_name"] = self._sheet_combo.currentText()

        if self._source_path and self._source_path.suffix.lower() == ".txt":
            idx = self._delimiter_combo.currentIndex()
            if 0 <= idx < len(_DELIMITERS):
                settings["delimiter"] = _DELIMITERS[idx][1]

        return settings

    @property
    def selected_columns(self) -> list[str]:
        """Return the list of currently selected column names."""
        return [
            cb.text().split("  ")[0]  # Strip type annotation
            for cb in self._checkboxes
            if cb.isChecked()
        ]

    @property
    def sensitive_columns(self) -> list[SensitiveColumn]:
        """Return detected sensitive columns."""
        return list(self._sensitive_results)

    # ── Setup ───────────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 28, 32, 28)
        root.setSpacing(0)

        # ── Header ──────────────────────────────────────────────────
        heading = QLabel("Preview & Configure")
        heading.setProperty("role", "heading")
        root.addWidget(heading)

        subtitle = QLabel(
            "Review your data, configure import settings, and select columns."
        )
        subtitle.setProperty("role", "subheading")
        subtitle.setContentsMargins(0, 4, 0, 0)
        root.addWidget(subtitle)

        root.addSpacing(20)

        # ── Import settings card ────────────────────────────────────
        settings_card = QFrame()
        settings_card.setProperty("role", "card")
        settings_layout = QHBoxLayout(settings_card)
        settings_layout.setContentsMargins(20, 14, 20, 14)
        settings_layout.setSpacing(24)

        # Header row selector
        header_section = QVBoxLayout()
        header_section.setSpacing(6)
        header_lbl = QLabel("Header Row")
        header_lbl.setProperty("role", "caption")
        header_section.addWidget(header_lbl)

        header_row_layout = QHBoxLayout()
        header_row_layout.setSpacing(8)

        self._header_group = QButtonGroup(self)
        self._header_first = QRadioButton("First row")
        self._header_first.setChecked(True)
        self._header_specific = QRadioButton("Row:")
        self._header_none = QRadioButton("No headers")
        self._header_group.addButton(self._header_first, 0)
        self._header_group.addButton(self._header_specific, 1)
        self._header_group.addButton(self._header_none, 2)

        self._header_spin = QSpinBox()
        self._header_spin.setMinimum(1)
        self._header_spin.setMaximum(100)
        self._header_spin.setValue(1)
        self._header_spin.setFixedWidth(60)
        self._header_spin.setEnabled(False)

        header_row_layout.addWidget(self._header_first)
        header_row_layout.addWidget(self._header_specific)
        header_row_layout.addWidget(self._header_spin)
        header_row_layout.addWidget(self._header_none)
        header_row_layout.addStretch()
        header_section.addLayout(header_row_layout)
        settings_layout.addLayout(header_section, stretch=2)

        # Separator
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.Shape.VLine)
        sep1.setProperty("role", "separator")
        settings_layout.addWidget(sep1)

        # Worksheet selector (XLSX only)
        self._sheet_section = QWidget()
        sheet_layout = QVBoxLayout(self._sheet_section)
        sheet_layout.setContentsMargins(0, 0, 0, 0)
        sheet_layout.setSpacing(6)
        sheet_lbl = QLabel("Worksheet")
        sheet_lbl.setProperty("role", "caption")
        sheet_layout.addWidget(sheet_lbl)
        self._sheet_combo = QComboBox()
        self._sheet_combo.setMinimumWidth(140)
        sheet_layout.addWidget(self._sheet_combo)
        self._sheet_section.setVisible(False)
        settings_layout.addWidget(self._sheet_section)

        # Delimiter selector (TXT only)
        self._delimiter_section = QWidget()
        delim_layout = QVBoxLayout(self._delimiter_section)
        delim_layout.setContentsMargins(0, 0, 0, 0)
        delim_layout.setSpacing(6)
        delim_lbl = QLabel("Delimiter")
        delim_lbl.setProperty("role", "caption")
        delim_layout.addWidget(delim_lbl)
        self._delimiter_combo = QComboBox()
        self._delimiter_combo.setMinimumWidth(120)
        for label, _ in _DELIMITERS:
            self._delimiter_combo.addItem(label)
        self._delimiter_section.setVisible(False)
        delim_layout.addWidget(self._delimiter_combo)
        settings_layout.addWidget(self._delimiter_section)

        root.addWidget(settings_card)

        # Connect signals
        self._header_group.buttonClicked.connect(self._on_header_changed)
        self._header_spin.valueChanged.connect(self._on_header_changed)
        self._sheet_combo.currentIndexChanged.connect(self._on_sheet_changed)
        self._delimiter_combo.currentIndexChanged.connect(
            self._on_delimiter_changed
        )

        root.addSpacing(12)

        # ── File info bar ───────────────────────────────────────────
        self._info_card = QFrame()
        self._info_card.setProperty("role", "card")
        info_layout = QHBoxLayout(self._info_card)
        info_layout.setContentsMargins(20, 12, 20, 12)
        info_layout.setSpacing(20)

        self._file_name_label = QLabel("No file loaded")
        self._file_name_label.setProperty("role", "subheading")
        info_layout.addWidget(self._file_name_label)

        self._file_size_label = QLabel("")
        self._file_size_label.setProperty("role", "caption")
        info_layout.addWidget(self._file_size_label)

        self._row_count_label = QLabel("")
        self._row_count_label.setProperty("role", "caption")
        info_layout.addWidget(self._row_count_label)

        self._type_info_label = QLabel("")
        self._type_info_label.setProperty("role", "caption")
        info_layout.addWidget(self._type_info_label)

        info_layout.addStretch()
        root.addWidget(self._info_card)

        root.addSpacing(12)

        # ── Main content: table + column sidebar ────────────────────
        content = QHBoxLayout()
        content.setSpacing(12)

        # Table
        self._model = DataFrameModel()
        self._table = FileTableView()
        self._table.setModel(self._model)
        self._table.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        content.addWidget(self._table, stretch=3)

        # Column selector panel
        col_panel = QFrame()
        col_panel.setProperty("role", "card")
        col_panel.setFixedWidth(280)
        col_panel_layout = QVBoxLayout(col_panel)
        col_panel_layout.setContentsMargins(16, 14, 16, 14)
        col_panel_layout.setSpacing(6)

        col_heading = QLabel("Columns")
        col_heading.setProperty("role", "subheading")
        col_panel_layout.addWidget(col_heading)

        # Separator
        sep2 = QFrame()
        sep2.setProperty("role", "separator")
        sep2.setFrameShape(QFrame.Shape.HLine)
        col_panel_layout.addWidget(sep2)

        # Select all
        self._select_all_cb = QCheckBox("Select All")
        self._select_all_cb.setChecked(True)
        self._select_all_cb.stateChanged.connect(self._on_select_all)
        col_panel_layout.addWidget(self._select_all_cb)

        # Scrollable checkbox area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self._cb_container = QWidget()
        self._cb_layout = QVBoxLayout(self._cb_container)
        self._cb_layout.setContentsMargins(0, 0, 0, 0)
        self._cb_layout.setSpacing(2)
        self._cb_layout.addStretch()
        scroll.setWidget(self._cb_container)
        col_panel_layout.addWidget(scroll)

        # Sensitive data warning area
        self._sensitive_frame = QFrame()
        self._sensitive_frame.setProperty("role", "card")
        sensitive_layout = QVBoxLayout(self._sensitive_frame)
        sensitive_layout.setContentsMargins(12, 10, 12, 10)
        sensitive_layout.setSpacing(4)
        sens_title = QLabel("⚠ Sensitive Data Detected")
        sens_title.setProperty("role", "caption")
        sens_title.setStyleSheet("color: #FBBF24; font-weight: 600;")
        sensitive_layout.addWidget(sens_title)
        self._sensitive_list_label = QLabel("")
        self._sensitive_list_label.setProperty("role", "caption")
        self._sensitive_list_label.setWordWrap(True)
        sensitive_layout.addWidget(self._sensitive_list_label)
        self._sensitive_frame.setVisible(False)
        col_panel_layout.addWidget(self._sensitive_frame)

        content.addWidget(col_panel)
        root.addLayout(content, stretch=1)

        # Placeholder text
        self._placeholder = QLabel(
            "Open a file to see the preview."
        )
        self._placeholder.setProperty("role", "caption")
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._placeholder.setMinimumHeight(200)
        # Show placeholder initially, hide table content
        self._table.hide()
        self._info_card.hide()
        root.addWidget(self._placeholder)

    # ── Internal ────────────────────────────────────────────────────

    def _get_header_row(self) -> int | None:
        """Return the header row index based on radio selection."""
        checked_id = self._header_group.checkedId()
        if checked_id == 0:  # First row
            return 0
        elif checked_id == 1:  # Specific row
            return self._header_spin.value() - 1  # Convert to 0-indexed
        else:  # No headers
            return None

    def _on_header_changed(self, *_args) -> None:
        self._header_spin.setEnabled(
            self._header_group.checkedId() == 1
        )
        if self._source_path:
            self._reload_preview()

    def _on_sheet_changed(self, _index: int) -> None:
        if self._source_path:
            self._reload_preview()

    def _on_delimiter_changed(self, _index: int) -> None:
        if self._source_path:
            self._reload_preview()

    def _reload_preview(self) -> None:
        """Reload the preview using current import settings."""
        if not self._source_path:
            return

        try:
            adapter = self._registry.get(self._source_path.suffix)
            kwargs = self.get_import_settings()
            df = adapter.read_preview(
                self._source_path, MAX_PREVIEW_ROWS, **kwargs
            )
        except Exception as exc:
            logger.exception("Failed to load preview for %s", self._source_path)
            QMessageBox.warning(
                self,
                "Load Error",
                f"Could not load file:\n\n{exc}",
            )
            return

        self._df = df
        self._model.update_dataframe(df)
        self._update_file_info(self._source_path, df)
        self._build_column_checkboxes(df)
        self._run_sensitive_detection(df)

    def _update_file_info(
        self, path: Path, df: pd.DataFrame
    ) -> None:
        self._file_name_label.setText(path.name)
        size = humanize_bytes(path.stat().st_size)
        self._file_size_label.setText(f"Size: {size}")
        self._row_count_label.setText(
            f"Rows: {len(df):,}  •  Columns: {len(df.columns)}"
        )

        # Data type summary
        type_counts = df.dtypes.value_counts()
        type_parts = [f"{count} {dtype}" for dtype, count in type_counts.items()]
        self._type_info_label.setText(
            "Types: " + ", ".join(type_parts)
        )

        # Show table, hide placeholder
        self._placeholder.hide()
        self._table.show()
        self._info_card.show()

    def _build_column_checkboxes(self, df: pd.DataFrame) -> None:
        # Clear existing
        for cb in self._checkboxes:
            self._cb_layout.removeWidget(cb)
            cb.deleteLater()
        self._checkboxes.clear()

        # Insert before the stretch
        for i, col in enumerate(df.columns):
            dtype = str(df[col].dtype)
            missing = df[col].isna().sum()
            label = f"{col}  ({dtype})"
            if missing > 0:
                label += f"  [{missing} missing]"
            cb = QCheckBox(label)
            cb.setChecked(True)
            cb.setToolTip(
                f"Column: {col}\n"
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

    def _run_sensitive_detection(self, df: pd.DataFrame) -> None:
        """Run PII detection and update the sensitive data panel."""
        self._sensitive_results = detect_sensitive_columns(df)

        if self._sensitive_results:
            lines = []
            for sc in self._sensitive_results[:8]:
                conf_pct = f"{sc.confidence:.0%}"
                lines.append(
                    f"• {sc.column_name} → {sc.category} ({conf_pct})"
                )
            self._sensitive_list_label.setText("\n".join(lines))
            self._sensitive_frame.setVisible(True)
        else:
            self._sensitive_frame.setVisible(False)

    def _on_select_all(self, state: int) -> None:
        checked = state == Qt.CheckState.Checked.value
        for cb in self._checkboxes:
            cb.blockSignals(True)
            cb.setChecked(checked)
            cb.blockSignals(False)
        self._emit_columns()

    def _on_column_toggled(self) -> None:
        all_checked = all(cb.isChecked() for cb in self._checkboxes)
        self._select_all_cb.blockSignals(True)
        self._select_all_cb.setChecked(all_checked)
        self._select_all_cb.blockSignals(False)
        self._emit_columns()

    def _emit_columns(self) -> None:
        self.columns_changed.emit(self.selected_columns)
