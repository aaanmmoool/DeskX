"""First-run welcome.

Three sentences about what DeskX is for, and a way to start with the
bundled sample instead of a real file.  The "don't show again"
preference is stored in the same ``QSettings`` store as before, so an
existing installation stays dismissed.
"""

from __future__ import annotations

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QCheckBox

from deskx.gui.theme import SPACE
from deskx.gui.theme.icons import Icon
from deskx.gui.widgets.components import (
    Button,
    Card,
    InfoNote,
    SectionHeader,
    label,
)
from deskx.gui.widgets.modal import ModalDialog

_SETTINGS_ORG = "DeskX"
_SETTINGS_APP = "DataSanitizer"
_FIRST_RUN_KEY = "first_run_completed"

_STEPS = (
    (
        Icon.UPLOAD,
        "Open a dataset",
        "Drag in a CSV, Excel, JSON, or text file. Nothing is uploaded — "
        "the file is read on this computer only.",
    ),
    (
        Icon.SHIELD,
        "Clean and protect it",
        "DeskX flags columns that look sensitive and offers plain-language "
        "rules to mask, redact, hash, or replace them.",
    ),
    (
        Icon.DOWNLOAD,
        "Save a separate copy",
        "You choose the name and folder. Your original file is never "
        "modified or overwritten.",
    ),
)


class WelcomeDialog(ModalDialog):
    """Shown once, on the first launch."""

    def __init__(self, parent=None) -> None:
        super().__init__(
            title="Welcome to DeskX",
            subtitle="Prepare your data safely, without it ever leaving this device.",
            icon=Icon.SPARKLE,
            width=620,
            primary_text="Get started",
            parent=parent,
        )
        self.setWindowTitle("Welcome to DeskX")
        self.load_sample_requested = False
        self.cancel_button.setVisible(False)

        for icon, title, text in _STEPS:
            card = Card(padding=SPACE.md, spacing=SPACE.xs, variant="cardFlat")
            card.add(SectionHeader(title, icon))
            card.add(label(text, "body", wrap=True))
            self.content.addWidget(card)

        self.content.addWidget(
            InfoNote(
                "DeskX works entirely offline. It makes no network requests.",
                variant="success",
                icon=Icon.LOCK,
            )
        )

        self._dont_show_cb = QCheckBox("Don't show this again")
        self._dont_show_cb.setChecked(True)
        self.add_footer_widget(self._dont_show_cb)

        self._sample_btn = Button("Try the sample data", icon=Icon.TABLE, role="ghost")
        self._sample_btn.clicked.connect(self._on_try_sample)
        self._footer_row.insertWidget(
            self._footer_row.count() - 2, self._sample_btn
        )

    # ── Actions ─────────────────────────────────────────────────────

    def _on_try_sample(self) -> None:
        self._save_preference()
        self.load_sample_requested = True
        self.accept()

    def _on_primary(self) -> None:
        self._save_preference()
        self.accept()

    def _save_preference(self) -> None:
        if self._dont_show_cb.isChecked():
            QSettings(_SETTINGS_ORG, _SETTINGS_APP).setValue(_FIRST_RUN_KEY, True)

    @staticmethod
    def should_show() -> bool:
        """Return ``True`` when the welcome has not been dismissed yet."""
        settings = QSettings(_SETTINGS_ORG, _SETTINGS_APP)
        return not settings.value(_FIRST_RUN_KEY, False, type=bool)
