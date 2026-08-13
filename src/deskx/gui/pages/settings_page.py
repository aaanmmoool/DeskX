"""Settings screen.

Only exposes preferences that already influence the app: the visual
theme, the folder the save dialog opens on, and whether the first-run
welcome is shown again.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSettings, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from deskx.core.config import APP_VERSION, get_app_data_dir, get_managed_output_dir
from deskx.gui.theme import SIZE, SPACE, ThemeMode
from deskx.gui.theme.icons import Icon
from deskx.gui.widgets.components import (
    Button,
    Card,
    ChipButton,
    InfoNote,
    SectionHeader,
    centered_page,
    label,
    scroll_container,
)

_SETTINGS_ORG = "DeskX"
_SETTINGS_APP = "DataSanitizer"
_LAST_DIR_KEY = "output/last_directory"
_FIRST_RUN_KEY = "first_run_completed"


class SettingsPage(QWidget):
    """Appearance and default save location.

    Signals
    -------
    theme_changed(object)
        Emitted with the chosen :class:`ThemeMode`.
    notify(str)
        Emitted with a short confirmation message.
    """

    theme_changed = Signal(object)
    notify = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._settings = QSettings(_SETTINGS_ORG, _SETTINGS_APP)
        self._setup_ui()

    # ── Public API ──────────────────────────────────────────────────

    def set_theme_mode(self, mode: ThemeMode) -> None:
        """Reflect the active theme without re-emitting a change."""
        is_light = mode is ThemeMode.LIGHT
        self._light_chip.setChecked(is_light)
        self._dark_chip.setChecked(not is_light)

    # ── Setup ───────────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        column = QWidget()
        column.setObjectName("pageRoot")
        col = QVBoxLayout(column)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(SPACE.lg)

        col.addWidget(label("Settings", "pageTitle"))
        col.addWidget(
            label(
                "DeskX stores these preferences on this computer only.",
                "subheading",
                wrap=True,
            )
        )

        col.addWidget(self._build_appearance_card())
        col.addWidget(self._build_location_card())
        col.addWidget(self._build_about_card())
        col.addStretch()

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(scroll_container(centered_page(column, max_width=820)))

    def _build_appearance_card(self) -> QWidget:
        card = Card(padding=SPACE.xl, spacing=SPACE.md)
        card.add(
            SectionHeader(
                "Appearance",
                Icon.SUN,
                "Choose the theme that is easiest on your eyes.",
            )
        )

        row = QHBoxLayout()
        row.setSpacing(SPACE.sm)

        self._light_chip = ChipButton("Light", Icon.SUN)
        self._light_chip.setChecked(True)
        self._light_chip.clicked.connect(
            lambda: self._choose_theme(ThemeMode.LIGHT)
        )
        row.addWidget(self._light_chip)

        self._dark_chip = ChipButton("Dark", Icon.MOON)
        self._dark_chip.clicked.connect(lambda: self._choose_theme(ThemeMode.DARK))
        row.addWidget(self._dark_chip)

        row.addStretch()
        card.add_layout(row)
        return card

    def _build_location_card(self) -> QWidget:
        card = Card(padding=SPACE.xl, spacing=SPACE.md)
        card.add(
            SectionHeader(
                "Default save location",
                Icon.FOLDER,
                "The folder the save dialog opens on. You can always change it "
                "for an individual file.",
            )
        )

        row = QHBoxLayout()
        row.setSpacing(SPACE.sm)

        self._location_edit = QLineEdit(self._current_default())
        self._location_edit.setMinimumHeight(SIZE.control_height_lg)
        self._location_edit.setPlaceholderText("Same folder as the source file")
        self._location_edit.editingFinished.connect(self._save_location)
        row.addWidget(self._location_edit, 1)

        browse = Button("Browse", icon=Icon.FOLDER_OPEN, height=SIZE.control_height_lg)
        browse.clicked.connect(self._browse)
        row.addWidget(browse)
        card.add_layout(row)

        chips = QHBoxLayout()
        chips.setSpacing(SPACE.sm)

        use_managed = Button(
            "Use the DeskX Output folder", icon=Icon.DOWNLOAD, role="ghost"
        )
        use_managed.setToolTip(str(get_managed_output_dir()))
        use_managed.clicked.connect(self._use_managed)
        chips.addWidget(use_managed)

        reset = Button("Reset to source folder", icon=Icon.REFRESH, role="ghost")
        reset.clicked.connect(self._reset_location)
        chips.addWidget(reset)

        chips.addStretch()
        card.add_layout(chips)

        card.add(
            InfoNote(
                "DeskX never writes over your source file. If a file with the "
                "same name already exists, you are asked what to do.",
                variant="info",
                icon=Icon.SHIELD,
            )
        )
        return card

    def _build_about_card(self) -> QWidget:
        card = Card(padding=SPACE.xl, spacing=SPACE.md)
        card.add(SectionHeader("About DeskX", Icon.INFO))
        card.add(label(f"Version {APP_VERSION}", "body"))
        card.add(
            label(
                f"Preferences and recent files are stored in {get_app_data_dir()}",
                "caption",
                wrap=True,
            )
        )

        row = QHBoxLayout()
        row.setSpacing(SPACE.sm)
        replay = Button("Show the welcome guide again", icon=Icon.SPARKLE, role="ghost")
        replay.clicked.connect(self._reset_first_run)
        row.addWidget(replay)
        row.addStretch()
        card.add_layout(row)
        return card

    # ── Actions ─────────────────────────────────────────────────────

    def _choose_theme(self, mode: ThemeMode) -> None:
        self.set_theme_mode(mode)
        self.theme_changed.emit(mode)

    def _current_default(self) -> str:
        return self._settings.value(_LAST_DIR_KEY, "", type=str)

    def _browse(self) -> None:
        start = self._location_edit.text().strip() or str(Path.home())
        chosen = QFileDialog.getExistingDirectory(
            self, "Choose a default save folder", start, QFileDialog.Option.ShowDirsOnly
        )
        if chosen:
            self._location_edit.setText(str(Path(chosen)))
            self._save_location()

    def _use_managed(self) -> None:
        self._location_edit.setText(str(get_managed_output_dir(create=True)))
        self._save_location()

    def _reset_location(self) -> None:
        self._location_edit.clear()
        self._settings.remove(_LAST_DIR_KEY)
        self.notify.emit("Saves will default to the source file's folder")

    def _save_location(self) -> None:
        text = self._location_edit.text().strip()
        if not text:
            self._settings.remove(_LAST_DIR_KEY)
            return
        if not Path(text).is_dir():
            self.notify.emit("That folder doesn't exist — nothing was saved")
            return
        self._settings.setValue(_LAST_DIR_KEY, text)
        self.notify.emit("Default save location updated")

    def _reset_first_run(self) -> None:
        self._settings.remove(_FIRST_RUN_KEY)
        self.notify.emit("The welcome guide will appear next time DeskX starts")
