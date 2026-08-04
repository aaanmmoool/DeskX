"""Compact summary card for configured transformation steps.

Displays a human-readable summary of an added transformation:
* Friendly Title
* Affected Columns
* Key configuration parameter summary
* Action buttons: Edit and Remove
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from deskx.processing.pipeline import TransformStep
from deskx.processing.transform_catalog import get_transform_metadata


class TransformSummaryCard(QFrame):
    """Card displaying summary of an active transform step in the sidebar."""

    edit_requested = Signal(object)  # Emits self.step
    remove_requested = Signal(object)  # Emits self.step

    def __init__(self, step: TransformStep, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.step = step
        self.metadata = get_transform_metadata(step.transform_type)
        self.setProperty("role", "card")
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        # Top row: Title + Actions
        top_row = QHBoxLayout()
        top_row.setSpacing(6)

        title_lbl = QLabel(f"✓  {self.metadata.friendly_name}")
        title_lbl.setStyleSheet("font-weight: 600; color: #34D399; font-size: 13px;")
        top_row.addWidget(title_lbl)
        top_row.addStretch()

        edit_btn = QPushButton("✏")
        edit_btn.setFixedSize(24, 24)
        edit_btn.setProperty("role", "ghost")
        edit_btn.setToolTip("Edit this transformation")
        edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        edit_btn.clicked.connect(lambda: self.edit_requested.emit(self.step))
        top_row.addWidget(edit_btn)

        remove_btn = QPushButton("✕")
        remove_btn.setFixedSize(24, 24)
        remove_btn.setProperty("role", "ghost")
        remove_btn.setToolTip("Remove from pipeline")
        remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        remove_btn.clicked.connect(lambda: self.remove_requested.emit(self.step))
        top_row.addWidget(remove_btn)

        layout.addLayout(top_row)

        # Columns line
        cols_text = self._format_columns()
        cols_lbl = QLabel(f"<b>Columns:</b> {cols_text}")
        cols_lbl.setProperty("role", "caption")
        cols_lbl.setWordWrap(True)
        layout.addWidget(cols_lbl)

        # Params line (if any)
        params_text = self._format_params()
        if params_text:
            params_lbl = QLabel(f"<b>Settings:</b> {params_text}")
            params_lbl.setProperty("role", "caption")
            params_lbl.setWordWrap(True)
            layout.addWidget(params_lbl)

    def _format_columns(self) -> str:
        p = self.step.params
        if "column" in p and p["column"]:
            return str(p["column"])
        if "columns" in p and p["columns"]:
            return ", ".join(p["columns"])
        if "subset" in p and p["subset"]:
            return ", ".join(p["subset"])
        return "All Columns"

    def _format_params(self) -> str:
        p = self.step.params
        parts = []
        for k, v in p.items():
            if k in {"column", "columns", "subset"}:
                continue
            parts.append(f"{k}: {v}")
        return ", ".join(parts)
