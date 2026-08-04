"""Help & User Guide Modal Dialog.

Provides an interactive built-in reference for first-time and business users,
explaining workflow, transformations, privacy detection, and shortcuts.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


class HelpDialog(QDialog):
    """Built-in interactive user guide dialog."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("DeskX — User Guide & Quick Start")
        self.setMinimumSize(640, 480)
        self.resize(700, 520)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header title
        header = QLabel("✦ DeskX Data Sanitizer Guide")
        header.setStyleSheet("font-size: 20px; font-weight: 600;")
        layout.addWidget(header)

        subhead = QLabel(
            "Welcome! DeskX helps you inspect, clean, and anonymize Excel and CSV data securely offline."
        )
        subhead.setProperty("role", "caption")
        subhead.setWordWrap(True)
        layout.addWidget(subhead)

        # Tabs
        tabs = QTabWidget()

        tabs.addTab(self._build_quick_start_tab(), "🚀 Quick Start")
        tabs.addTab(self._build_transforms_tab(), "⚡ Transformations")
        tabs.addTab(self._build_privacy_tab(), "🛡 Privacy & Detection")
        tabs.addTab(self._build_shortcuts_tab(), "⌨ Shortcuts")

        layout.addWidget(tabs, stretch=1)

        # Bottom button box
        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        btn_box.rejected.connect(self.accept)
        layout.addWidget(btn_box)

    def _build_scrollable_page(self, content_widget: QWidget) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(content_widget)
        return scroll

    def _build_quick_start_tab(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        steps = [
            (
                "1. Load Your Dataset",
                "Click Browse or drag & drop any Excel (.xlsx), CSV (.csv), or Text (.txt) file onto the upload area. "
                "You can also select from Recent Files or try a bundled Sample Dataset to experiment.",
            ),
            (
                "2. Configure & Clean",
                "On the configure screen, review your data in the live preview table. Use the right-hand panel to:\n"
                "• Toggle columns on/off to include or drop them.\n"
                "• Click '+ Add' to attach data cleaning rules (like Trim Whitespace or Deduplicate Rows).\n"
                "• Click 'Edit' (✏) on any transformation card to preview its effect on live sample data.",
            ),
            (
                "3. Protect Sensitive Data",
                "DeskX automatically scans your headers and rows for sensitive PII (Emails, Names, SSNs, Credit Cards). "
                "Use the yellow Sensitive Columns toolbar to apply one-click protection: Masking, Redaction, Hashing, or Pseudonymizing.",
            ),
            (
                "4. Export & Audit",
                "When ready, click 'Process & Export' to save your sanitized dataset. DeskX generates an accompanying "
                "JSON compliance audit report logging every applied transformation.",
            ),
        ]

        for title, desc in steps:
            card = QFrame()
            card.setProperty("role", "card")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(14, 12, 14, 12)
            card_layout.setSpacing(6)

            lbl_title = QLabel(title)
            lbl_title.setStyleSheet("font-weight: 600; font-size: 14px; color: #60A5FA;")
            card_layout.addWidget(lbl_title)

            lbl_desc = QLabel(desc)
            lbl_desc.setWordWrap(True)
            card_layout.addWidget(lbl_desc)

            layout.addWidget(card)

        layout.addStretch()
        return self._build_scrollable_page(container)

    def _build_transforms_tab(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        categories = [
            (
                "Data Cleaning",
                "• Trim Whitespace: Removes leading/trailing spaces from text cells and column names.\n"
                "• Remove Empty Rows/Columns: Drops rows or columns that are entirely empty.\n"
                "• Remove Duplicates: Finds duplicate rows and keeps only the first or last occurrence.\n"
                "• Fill Missing Values: Replaces empty cells with a custom value, mean, or median.",
            ),
            (
                "Privacy & Security",
                "• Mask Column: Replaces all but the last 4 characters with asterisks (e.g., *******1234).\n"
                "• Redact Column: Replaces the entire cell value with [REDACTED].\n"
                "• Hash Column: Generates a deterministic SHA-256 fingerprint of the value.\n"
                "• Pseudonymize: Consistently maps unique names/IDs to realistic fictional aliases.",
            ),
            (
                "Formatting & Transformations",
                "• Rename Columns: Maps old header names to new names.\n"
                "• Reorder Columns: Moves specified columns to the front of the dataset.\n"
                "• Revenue Bands: Categorizes numeric values into Low, Medium, High, or Enterprise bands.\n"
                "• Suppress Low Counts: Replaces rare categories occurring fewer than N times with 'Other'.",
            ),
        ]

        for cat, text in categories:
            card = QFrame()
            card.setProperty("role", "card")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(14, 12, 14, 12)
            card_layout.setSpacing(6)

            lbl_title = QLabel(cat)
            lbl_title.setStyleSheet("font-weight: 600; font-size: 14px; color: #34D399;")
            card_layout.addWidget(lbl_title)

            lbl_desc = QLabel(text)
            lbl_desc.setWordWrap(True)
            card_layout.addWidget(lbl_desc)

            layout.addWidget(card)

        layout.addStretch()
        return self._build_scrollable_page(container)

    def _build_privacy_tab(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        info_card = QFrame()
        info_card.setProperty("role", "card")
        info_layout = QVBoxLayout(info_card)
        info_layout.setContentsMargins(14, 12, 14, 12)
        info_layout.setSpacing(8)

        lbl1 = QLabel("Automatic PII & Sensitive Column Detection")
        lbl1.setStyleSheet("font-weight: 600; font-size: 14px; color: #FBBF24;")
        info_layout.addWidget(lbl1)

        lbl2 = QLabel(
            "Whenever you load a file, DeskX scans both column headers and cell values using pattern matching "
            "and statistical heuristics to detect:\n\n"
            "• Email Addresses (e.g., user@example.com)\n"
            "• Person Names & Employee IDs\n"
            "• Financial Information (Credit Cards, IBANs, Bank Accounts)\n"
            "• Government IDs (SSN, Passport numbers)\n"
            "• Phone Numbers & Postal Addresses\n\n"
            "When sensitive columns are found, a warning banner appears in the sidebar. You can choose "
            "a suggested action (Mask, Redact, Hash, Pseudonymize) from the dropdown to protect that column instantly."
        )
        lbl2.setWordWrap(True)
        info_layout.addWidget(lbl2)

        layout.addWidget(info_card)
        layout.addStretch()
        return self._build_scrollable_page(container)

    def _build_shortcuts_tab(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        shortcuts = [
            ("Ctrl + O", "Open file browse dialog"),
            ("Ctrl + E / Ctrl + S", "Export and save processed dataset"),
            ("F1", "Open this User Guide dialog"),
            ("Escape", "Close active modal dialog or return to previous screen"),
        ]

        card = QFrame()
        card.setProperty("role", "card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(14, 12, 14, 12)
        card_layout.setSpacing(10)

        title = QLabel("Keyboard Shortcuts")
        title.setStyleSheet("font-weight: 600; font-size: 14px; color: #A78BFA;")
        card_layout.addWidget(title)

        for key, desc in shortcuts:
            row = QFrame()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 4, 0, 4)

            k_lbl = QLabel(f"  {key}  ")
            k_lbl.setStyleSheet(
                "background-color: #2D313E; border: 1px solid #4B5563; "
                "border-radius: 4px; font-family: monospace; font-weight: 600;"
            )
            k_lbl.setFixedWidth(140)
            row_layout.addWidget(k_lbl)

            d_lbl = QLabel(desc)
            row_layout.addWidget(d_lbl, stretch=1)

            card_layout.addWidget(row)

        layout.addWidget(card)
        layout.addStretch()
        return self._build_scrollable_page(container)
