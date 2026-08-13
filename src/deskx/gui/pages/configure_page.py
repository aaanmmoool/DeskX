"""Configure screen — the main workspace.

One toolbar and three tabs, so the window is never crowded:

* **Preview** — how DeskX reads the file, plus the data itself
* **Transformations** — detected sensitive columns, the rule catalog,
  and the pipeline being assembled
* **Review** — a plain visual summary of what will happen

The reading, detection, and transformation logic is unchanged; this
module only decides how it is presented.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLineEdit,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from deskx.adapters.adapter_registry import create_default_registry
from deskx.core.config import MAX_PREVIEW_ROWS, SANITIZED_SUFFIX
from deskx.core.utils import build_output_filename, humanize_bytes
from deskx.gui.theme import ColorPalette, SIZE, SPACE, palette
from deskx.gui.theme.icons import Icon, get_icon, get_pixmap, icon_label
from deskx.gui.widgets.column_select_dialog import ColumnSelectDialog
from deskx.gui.widgets.components import (
    Badge,
    Button,
    Card,
    IconButton,
    InfoNote,
    SectionHeader,
    StepIndicator,
    Themed,
    centered_page,
    clear_layout,
    label,
    scroll_container,
)
from deskx.gui.widgets.file_table import DataFrameModel, FileTableView
from deskx.gui.workflow import STEP_PREVIEW, WORKFLOW_STEPS
from deskx.gui.widgets.transform_sidebar import TransformSidebar
from deskx.gui.widgets.transform_summary_card import icon_for
from deskx.processing.pipeline import TransformStep
from deskx.processing.sensitive_detector import (
    SensitiveColumn,
    detect_sensitive_columns,
)
from deskx.processing.transform_catalog import get_transform_metadata

logger = logging.getLogger(__name__)

_DELIMITERS = [
    ("Tab (\\t)", "\t"),
    ("Comma (,)", ","),
    ("Semicolon (;)", ";"),
    ("Pipe (|)", "|"),
    ("Space", " "),
]

_HEADER_CHOICES = [
    ("First row is the header", 0),
    ("Header is on a specific row", 1),
    ("There is no header row", 2),
]

_PAGE_SIZES = ["25", "50", "100", "500"]

# Below this the toolbar needs the space for the file name and the CTA.
_STEPS_MIN_WIDTH = 1080


class ConfigurePage(QWidget, Themed):
    """Preview, configure, and review — all on one screen.

    Signals
    -------
    back_requested()
        The user wants to pick a different file.
    process_requested()
        The user is ready to choose a destination and process.
    """

    back_requested = Signal()
    process_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._registry = create_default_registry()
        self._df: pd.DataFrame | None = None
        self._source_path: Path | None = None
        self._column_states: dict[str, bool] = {}
        self._sensitive_results: list[SensitiveColumn] = []
        self._current_page: int = 0
        self._setup_ui()
        self._register_theme()

    # ── Public API ──────────────────────────────────────────────────

    def load_file(self, path: str) -> None:
        """Load a file and populate every part of the workspace."""
        file_path = Path(path)
        self._source_path = file_path

        self._file_name.setText(file_path.name)
        self._file_name.setToolTip(str(file_path))
        try:
            self._size_badge.setText(humanize_bytes(file_path.stat().st_size))
            self._size_badge.setVisible(True)
        except OSError:
            self._size_badge.setVisible(False)

        ext = file_path.suffix.lower()
        self._format_badge.setText(ext.lstrip(".").upper())
        self._sheet_row.setVisible(ext == ".xlsx")
        self._delim_row.setVisible(ext == ".txt")

        if ext == ".xlsx":
            self._load_sheet_names(file_path, ext)
        if ext == ".txt":
            self._autodetect_delimiter(file_path, ext)

        self._error_banner.setVisible(False)
        self._tabs.setCurrentIndex(0)
        self._steps.set_current(STEP_PREVIEW)

        self._reload_preview()

    def get_import_settings(self) -> dict:
        """Return the current import settings for the processing job."""
        settings = {"header_row": self._get_header_row()}

        if self._source_path and self._source_path.suffix.lower() == ".xlsx":
            settings["sheet_name"] = self._sheet_combo.currentText()

        if self._source_path and self._source_path.suffix.lower() == ".txt":
            index = self._delim_combo.currentIndex()
            if 0 <= index < len(_DELIMITERS):
                settings["delimiter"] = _DELIMITERS[index][1]

        return settings

    def get_selected_columns(self) -> list[str]:
        """Return the columns the user chose to keep."""
        return [name for name, keep in self._column_states.items() if keep]

    def get_transform_steps(self) -> list[TransformStep]:
        """Return the configured transformation pipeline."""
        return self._transform_sidebar.get_pipeline()

    def set_processing(self, running: bool) -> None:
        """Toggle the workspace's interactive state during processing."""
        self._process_btn.setEnabled(not running)
        # "&&" renders as a literal ampersand instead of a mnemonic.
        self._process_btn.setText("Processing…" if running else "Process && Save")
        self._back_btn.setEnabled(not running)
        self._tabs.setEnabled(not running)

    def show_success(self, output_path: str, row_count: int | None) -> None:
        """Kept for compatibility — results now live on their own screen."""
        self._error_banner.setVisible(False)

    def show_error(self, message: str) -> None:
        """Surface a processing failure inline, above the tabs."""
        self._error_banner.set_message(message, "error")
        self._error_banner.setVisible(True)

    @property
    def sensitive_columns(self) -> list[SensitiveColumn]:
        return list(self._sensitive_results)

    @property
    def dataframe(self) -> pd.DataFrame | None:
        return self._df

    # ── Setup ───────────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(SPACE.xxl, SPACE.xl, SPACE.xxl, SPACE.lg)
        root.setSpacing(SPACE.md)

        root.addWidget(self._build_toolbar())

        self._error_banner = InfoNote("", variant="error", icon=Icon.ERROR)
        self._error_banner.setVisible(False)
        root.addWidget(self._error_banner)

        self._tabs = QTabWidget()
        self._tabs.setDocumentMode(True)
        self._tabs.addTab(self._build_preview_tab(), "Preview")
        self._tabs.addTab(self._build_transform_tab(), "Transformations")
        self._tabs.addTab(self._build_review_tab(), "Review")
        self._tabs.currentChanged.connect(self._on_tab_changed)
        root.addWidget(self._tabs, 1)

    def _build_toolbar(self) -> QWidget:
        bar = QWidget()
        row = QHBoxLayout(bar)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(SPACE.md)

        self._back_btn = Button("Back", icon=Icon.ARROW_LEFT, role="ghost")
        self._back_btn.setToolTip("Choose a different file")
        self._back_btn.clicked.connect(self.back_requested.emit)
        row.addWidget(self._back_btn)

        self._file_icon = icon_label(Icon.FILE, palette().primary, SIZE.icon_lg)
        row.addWidget(self._file_icon)

        info_col = QVBoxLayout()
        info_col.setContentsMargins(0, 0, 0, 0)
        info_col.setSpacing(0)
        self._file_name = label("No file loaded", "cardTitle")
        info_col.addWidget(self._file_name)

        meta_row = QHBoxLayout()
        meta_row.setContentsMargins(0, 0, 0, 0)
        meta_row.setSpacing(SPACE.xs + 2)
        self._format_badge = Badge("", "primary")
        self._size_badge = Badge("", "neutral")
        self._shape_badge = Badge("", "neutral")
        for badge in (self._format_badge, self._size_badge, self._shape_badge):
            meta_row.addWidget(badge)
        meta_row.addStretch()
        info_col.addLayout(meta_row)
        row.addLayout(info_col)

        row.addStretch()

        self._steps = StepIndicator(WORKFLOW_STEPS)
        self._steps.set_current(STEP_PREVIEW)
        row.addWidget(self._steps)

        self._process_btn = Button(
            "Process && Save",
            icon=Icon.PROCESS,
            role="primary",
            height=SIZE.control_height_lg,
        )
        self._process_btn.setMinimumWidth(170)
        self._process_btn.setToolTip("Choose a destination, then run the pipeline")
        self._process_btn.clicked.connect(self.process_requested.emit)
        row.addWidget(self._process_btn)

        return bar

    # ── Preview tab ─────────────────────────────────────────────────

    def _build_preview_tab(self) -> QWidget:
        page = QWidget()
        page.setObjectName("pageRoot")
        col = QVBoxLayout(page)
        col.setContentsMargins(SPACE.lg, SPACE.lg, SPACE.lg, SPACE.lg)
        col.setSpacing(SPACE.md)

        col.addWidget(self._build_import_bar())

        self._model = DataFrameModel()
        self._table = FileTableView()
        self._table.setModel(self._model)
        col.addWidget(self._table, 1)

        col.addWidget(self._build_table_footer())
        return page

    def _build_import_bar(self) -> QWidget:
        card = Card(padding=SPACE.md, spacing=SPACE.sm, variant="cardFlat")
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(SPACE.md)

        row.addWidget(icon_label(Icon.SETTINGS, palette().text_secondary, SIZE.icon_md))
        row.addWidget(label("How to read this file", "body"))

        self._header_combo = QComboBox()
        for text, _ in _HEADER_CHOICES:
            self._header_combo.addItem(text)
        self._header_combo.setToolTip(
            "Tells DeskX which row holds your column titles."
        )
        self._header_combo.setMinimumWidth(200)
        row.addWidget(self._header_combo)

        self._header_spin = QSpinBox()
        self._header_spin.setRange(1, 100)
        self._header_spin.setValue(1)
        self._header_spin.setPrefix("Row ")
        self._header_spin.setFixedWidth(88)
        self._header_spin.setEnabled(False)
        row.addWidget(self._header_spin)

        self._sheet_row = QWidget()
        sheet_layout = QHBoxLayout(self._sheet_row)
        sheet_layout.setContentsMargins(0, 0, 0, 0)
        sheet_layout.setSpacing(SPACE.xs + 2)
        sheet_layout.addWidget(label("Sheet", "caption"))
        self._sheet_combo = QComboBox()
        self._sheet_combo.setMinimumWidth(140)
        sheet_layout.addWidget(self._sheet_combo)
        self._sheet_row.setVisible(False)
        row.addWidget(self._sheet_row)

        self._delim_row = QWidget()
        delim_layout = QHBoxLayout(self._delim_row)
        delim_layout.setContentsMargins(0, 0, 0, 0)
        delim_layout.setSpacing(SPACE.xs + 2)
        delim_layout.addWidget(label("Separator", "caption"))
        self._delim_combo = QComboBox()
        self._delim_combo.setMinimumWidth(130)
        for text, _ in _DELIMITERS:
            self._delim_combo.addItem(text)
        delim_layout.addWidget(self._delim_combo)
        self._delim_row.setVisible(False)
        row.addWidget(self._delim_row)

        row.addStretch()

        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("Search all columns…")
        self._search_edit.setClearButtonEnabled(True)
        self._search_edit.setMinimumWidth(240)
        self._search_edit.setMinimumHeight(SIZE.control_height)
        self._search_edit.addAction(
            _search_action(self), QLineEdit.ActionPosition.LeadingPosition
        )
        self._search_edit.textChanged.connect(
            lambda: self._update_table_view(reset_page=True)
        )
        row.addWidget(self._search_edit)

        card.add_layout(row)

        self._header_combo.currentIndexChanged.connect(self._on_settings_changed)
        self._header_spin.valueChanged.connect(self._on_settings_changed)
        self._sheet_combo.currentIndexChanged.connect(self._on_settings_changed)
        self._delim_combo.currentIndexChanged.connect(self._on_settings_changed)
        return card

    def _build_table_footer(self) -> QWidget:
        bar = QWidget()
        row = QHBoxLayout(bar)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(SPACE.sm)

        self._columns_label = label("", "caption")
        row.addWidget(self._columns_label)

        choose = Button("Choose columns", icon=Icon.COLUMNS, role="ghost")
        choose.setToolTip("Pick which columns end up in the sanitized copy")
        choose.clicked.connect(self._open_column_picker)
        row.addWidget(choose)

        row.addStretch()

        row.addWidget(label("Rows per page", "caption"))
        self._page_size_combo = QComboBox()
        self._page_size_combo.addItems(_PAGE_SIZES)
        self._page_size_combo.setCurrentText("50")
        self._page_size_combo.setFixedWidth(76)
        self._page_size_combo.currentTextChanged.connect(
            lambda: self._update_table_view(reset_page=True)
        )
        row.addWidget(self._page_size_combo)

        self._prev_page_btn = IconButton(Icon.CHEVRON_LEFT, "Previous page", 30)
        self._prev_page_btn.clicked.connect(self._on_prev_page)
        row.addWidget(self._prev_page_btn)

        self._page_label = label("Page 1 of 1", "caption")
        self._page_label.setMinimumWidth(150)
        self._page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        row.addWidget(self._page_label)

        self._next_page_btn = IconButton(Icon.CHEVRON_RIGHT, "Next page", 30)
        self._next_page_btn.clicked.connect(self._on_next_page)
        row.addWidget(self._next_page_btn)

        return bar

    # ── Transformations tab ─────────────────────────────────────────

    def _build_transform_tab(self) -> QWidget:
        self._transform_sidebar = TransformSidebar()
        self._transform_sidebar.pipeline_changed.connect(self._on_pipeline_changed)

        holder = QWidget()
        holder.setObjectName("pageRoot")
        col = QVBoxLayout(holder)
        col.setContentsMargins(0, SPACE.lg, 0, SPACE.lg)
        col.setSpacing(0)
        col.addWidget(self._transform_sidebar)
        col.addStretch()

        return scroll_container(
            centered_page(holder, max_width=980, margins=(SPACE.xxl, 0, SPACE.xxl, 0))
        )

    # ── Review tab ──────────────────────────────────────────────────

    def _build_review_tab(self) -> QWidget:
        holder = QWidget()
        holder.setObjectName("pageRoot")
        col = QVBoxLayout(holder)
        col.setContentsMargins(0, SPACE.lg, 0, SPACE.lg)
        col.setSpacing(SPACE.md)

        col.addWidget(
            SectionHeader(
                "What will happen",
                Icon.PIPELINE,
                "DeskX reads your file, runs these steps on a copy, and writes "
                "a new file. The original is never modified.",
                title_role="sectionTitle",
            )
        )

        self._review_layout = QVBoxLayout()
        self._review_layout.setSpacing(SPACE.sm)
        col.addLayout(self._review_layout)

        col.addStretch()

        return scroll_container(
            centered_page(holder, max_width=760, margins=(SPACE.xxl, 0, SPACE.xxl, 0))
        )

    def _rebuild_review(self) -> None:
        clear_layout(self._review_layout)

        if self._source_path is None:
            return

        rows = len(self._df) if self._df is not None else None
        kept = len(self.get_selected_columns())
        total = len(self._column_states)
        detail = f"{rows:,} rows previewed" if rows is not None else ""
        if total and kept < total:
            detail += f"   ·   {kept} of {total} columns kept"

        self._review_layout.addWidget(
            _pipeline_node(
                "INPUT",
                self._source_path.name,
                detail,
                Icon.FILE,
                "primary",
            )
        )

        cards = self._transform_sidebar.pipeline_cards()
        if not cards:
            self._review_layout.addWidget(_arrow_row())
            self._review_layout.addWidget(
                _pipeline_node(
                    "NO CHANGES",
                    "Copy the data as-is",
                    "Add a transformation to clean or protect values.",
                    Icon.INFO,
                    "text_secondary",
                )
            )
        for card in cards:
            metadata = get_transform_metadata(card.step.transform_type)
            summary = card.friendly_params()
            columns = card._format_columns()
            detail = f"on {columns}"
            if summary:
                detail += f"   ·   {summary}"
            self._review_layout.addWidget(_arrow_row())
            self._review_layout.addWidget(
                _pipeline_node(
                    metadata.category.upper(),
                    metadata.friendly_name,
                    detail,
                    icon_for(metadata),
                    "secondary",
                )
            )

        self._review_layout.addWidget(_arrow_row())
        self._review_layout.addWidget(
            _pipeline_node(
                "OUTPUT",
                build_output_filename(self._source_path, SANITIZED_SUFFIX),
                "You choose the folder in the next step.",
                Icon.DOWNLOAD,
                "success",
            )
        )

    # ── Internal ────────────────────────────────────────────────────

    def _load_sheet_names(self, file_path: Path, ext: str) -> None:
        try:
            adapter = self._registry.get(ext)
            sheets = adapter.get_sheet_names(file_path)
            self._sheet_combo.blockSignals(True)
            self._sheet_combo.clear()
            self._sheet_combo.addItems(sheets)
            self._sheet_combo.blockSignals(False)
        except Exception:
            logger.exception("Failed to read sheet names")

    def _autodetect_delimiter(self, file_path: Path, ext: str) -> None:
        try:
            adapter = self._registry.get(ext)
            detected = adapter.detect_delimiter(file_path)
            if not detected:
                return
            for index, (_, delimiter) in enumerate(_DELIMITERS):
                if delimiter == detected:
                    self._delim_combo.blockSignals(True)
                    self._delim_combo.setCurrentIndex(index)
                    self._delim_combo.blockSignals(False)
                    break
        except Exception:
            logger.exception("Failed to detect delimiter")

    def _get_header_row(self) -> int | None:
        choice = _HEADER_CHOICES[self._header_combo.currentIndex()][1]
        if choice == 0:
            return 0
        if choice == 1:
            return self._header_spin.value() - 1
        return None

    def _on_settings_changed(self, *_args) -> None:
        self._header_spin.setEnabled(
            _HEADER_CHOICES[self._header_combo.currentIndex()][1] == 1
        )
        if self._source_path:
            self._reload_preview()

    def _reload_preview(self) -> None:
        if not self._source_path:
            return

        try:
            adapter = self._registry.get(self._source_path.suffix)
            kwargs = self.get_import_settings()
            df = adapter.read_preview(self._source_path, MAX_PREVIEW_ROWS, **kwargs)
        except Exception as exc:
            logger.exception("Failed to load preview")
            self.show_error(f"DeskX could not read this file: {exc}")
            return

        self._error_banner.setVisible(False)
        self._df = df
        self._transform_sidebar.set_sample_data(df)
        self._sync_column_states(df)
        self._update_table_view(reset_page=True)
        self._update_shape_badge(df)
        self._run_sensitive_detection(df)
        self._transform_sidebar.set_columns([str(c) for c in df.columns])
        self._rebuild_review()

    def _sync_column_states(self, df: pd.DataFrame) -> None:
        """Keep previously excluded columns excluded across reloads."""
        previous = dict(self._column_states)
        self._column_states = {
            str(column): previous.get(str(column), True) for column in df.columns
        }
        self._update_columns_label()

    def _update_columns_label(self) -> None:
        total = len(self._column_states)
        kept = len(self.get_selected_columns())
        if not total:
            self._columns_label.setText("")
        elif kept == total:
            self._columns_label.setText(f"All {total} columns included")
        else:
            self._columns_label.setText(
                f"{kept} of {total} columns included  ·  {total - kept} dropped"
            )

    def _open_column_picker(self) -> None:
        if self._df is None:
            return
        dialog = ColumnSelectDialog(
            self._df, self._column_states, self._sensitive_results, parent=self
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._column_states = dialog.selection()
            self._update_columns_label()
            self._rebuild_review()

    def _on_prev_page(self) -> None:
        self._current_page = max(0, self._current_page - 1)
        self._update_table_view(reset_page=False)

    def _on_next_page(self) -> None:
        self._current_page += 1
        self._update_table_view(reset_page=False)

    def _update_table_view(self, reset_page: bool = True) -> None:
        if self._df is None or self._df.empty:
            if self._df is not None:
                self._model.update_dataframe(self._df)
            self._page_label.setText("No rows")
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

        start = self._current_page * page_size
        self._model.update_dataframe(filtered_df.iloc[start : start + page_size])

        self._page_label.setText(
            f"Page {self._current_page + 1} of {total_pages}  ·  "
            f"{len(filtered_df):,} rows"
        )
        self._prev_page_btn.setEnabled(self._current_page > 0)
        self._next_page_btn.setEnabled(self._current_page < total_pages - 1)

    def _update_shape_badge(self, df: pd.DataFrame) -> None:
        self._shape_badge.setText(
            f"{len(df):,} rows × {len(df.columns)} columns"
        )

    def _run_sensitive_detection(self, df: pd.DataFrame) -> None:
        self._sensitive_results = detect_sensitive_columns(df)
        self._transform_sidebar.set_sensitive_columns(self._sensitive_results)

        count = len(self._sensitive_results)
        if count:
            self._tabs.setTabText(1, f"Transformations  ({count} to review)")
        else:
            self._tabs.setTabText(1, "Transformations")

    def _on_pipeline_changed(self, _steps: list) -> None:
        self._rebuild_review()

    def _on_tab_changed(self, index: int) -> None:
        self._steps.set_current(STEP_PREVIEW + index)
        if index == 2:
            self._rebuild_review()

    def apply_theme(self, p: ColorPalette) -> None:
        self._file_icon.setPixmap(get_pixmap(Icon.FILE, p.primary, SIZE.icon_lg))

    def resizeEvent(self, event) -> None:
        """Drop the breadcrumb on narrow windows rather than squash it."""
        super().resizeEvent(event)
        self._steps.setVisible(self.width() >= _STEPS_MIN_WIDTH)


# ── Review helpers ──────────────────────────────────────────────────


def _pipeline_node(
    eyebrow: str,
    title: str,
    detail: str,
    icon: str,
    tone: str,
) -> QWidget:
    """One node in the review pipeline."""
    card = Card(padding=SPACE.md, spacing=0)
    row = QHBoxLayout()
    row.setContentsMargins(0, 0, 0, 0)
    row.setSpacing(SPACE.md)

    color = getattr(palette(), tone, palette().primary)
    row.addWidget(icon_label(icon, color, SIZE.icon_lg), 0, Qt.AlignmentFlag.AlignTop)

    col = QVBoxLayout()
    col.setContentsMargins(0, 0, 0, 0)
    col.setSpacing(1)
    col.addWidget(label(eyebrow, "eyebrow"))
    col.addWidget(label(title, "cardTitle"))
    if detail:
        col.addWidget(label(detail, "caption", wrap=True))
    row.addLayout(col, 1)

    card.add_layout(row)
    return card


def _arrow_row() -> QWidget:
    """The connector drawn between two pipeline nodes."""
    holder = QWidget()
    row = QHBoxLayout(holder)
    row.setContentsMargins(SPACE.xxl, 0, 0, 0)
    row.setSpacing(0)
    row.addWidget(icon_label(Icon.ARROW_DOWN, palette().text_tertiary, SIZE.icon_md))
    row.addStretch()
    holder.setFixedHeight(SIZE.icon_md + SPACE.xs)
    return holder


def _search_action(parent: QWidget) -> QAction:
    """A leading search glyph for the preview search field."""
    action = QAction(parent)
    action.setIcon(get_icon(Icon.SEARCH, palette().text_tertiary, SIZE.icon_sm))
    return action
