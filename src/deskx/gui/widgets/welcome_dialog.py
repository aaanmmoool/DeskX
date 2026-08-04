"""First-Run Onboarding Welcome Dialog.

Shown automatically on the user's first launch of DeskX to explain key concepts
in 3 simple steps. Includes an option to load a sample dataset immediately.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QSettings
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)


class WelcomeDialog(QDialog):
    """3-step welcome and onboarding dialog for first-time users."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Welcome to DeskX Data Sanitizer")
        self.setMinimumWidth(560)
        self.resize(600, 440)
        self.load_sample_requested = False
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 20)
        layout.setSpacing(16)

        # Title
        title = QLabel("✦ Welcome to DeskX")
        title.setStyleSheet("font-size: 22px; font-weight: 700; color: #60A5FA;")
        layout.addWidget(title)

        subtitle = QLabel(
            "Your offline desktop workspace for data cleaning, anonymization, and compliance auditing."
        )
        subtitle.setProperty("role", "caption")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        # 3 Steps cards
        steps_layout = QVBoxLayout()
        steps_layout.setSpacing(10)

        steps = [
            (
                "1. Load Your Dataset",
                "Drop an Excel (.xlsx), CSV, or Text file into DeskX. All processing runs 100% locally on your computer—your data never leaves your machine.",
                "#3B82F6",
            ),
            (
                "2. Clean & Anonymize Data",
                "DeskX detects sensitive PII (Emails, Names, SSNs, Bank details) automatically. Apply masking, redaction, deduplication, and formatting rules with one click.",
                "#10B981",
            ),
            (
                "3. Preview Live & Export",
                "Preview transformation results in real-time. Export your sanitized dataset along with a compliance JSON audit trail.",
                "#A855F7",
            ),
        ]

        for step_title, step_desc, color in steps:
            card = QFrame()
            card.setProperty("role", "card")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(16, 12, 16, 12)
            card_layout.setSpacing(4)

            lbl_title = QLabel(step_title)
            lbl_title.setStyleSheet(f"font-weight: 600; font-size: 14px; color: {color};")
            card_layout.addWidget(lbl_title)

            lbl_desc = QLabel(step_desc)
            lbl_desc.setProperty("role", "caption")
            lbl_desc.setWordWrap(True)
            card_layout.addWidget(lbl_desc)

            steps_layout.addWidget(card)

        layout.addLayout(steps_layout)

        layout.addStretch()

        # Bottom controls
        bot_layout = QHBoxLayout()

        self._dont_show_cb = QCheckBox("Don't show this message again on startup")
        self._dont_show_cb.setChecked(True)
        bot_layout.addWidget(self._dont_show_cb)

        bot_layout.addStretch()

        sample_btn = QPushButton("🎁 Try Sample Dataset")
        sample_btn.setProperty("role", "ghost")
        sample_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        sample_btn.clicked.connect(self._on_try_sample)
        bot_layout.addWidget(sample_btn)

        start_btn = QPushButton("Get Started →")
        start_btn.setProperty("role", "primary")
        start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        start_btn.clicked.connect(self._on_get_started)
        bot_layout.addWidget(start_btn)

        layout.addLayout(bot_layout)

    def _on_try_sample(self) -> None:
        self._save_preference()
        self.load_sample_requested = True
        self.accept()

    def _on_get_started(self) -> None:
        self._save_preference()
        self.accept()

    def _save_preference(self) -> None:
        settings = QSettings("DeskX", "DataSanitizer")
        if self._dont_show_cb.isChecked():
            settings.setValue("first_run_completed", True)

    @staticmethod
    def should_show() -> bool:
        """Check if the welcome dialog has already been shown and dismissed."""
        settings = QSettings("DeskX", "DataSanitizer")
        return not settings.value("first_run_completed", False, type=bool)
