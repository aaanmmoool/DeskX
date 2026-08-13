"""Save-destination modal shown immediately before processing starts.

The user confirms three things before a single byte is written:

* which file is being read (never modified),
* what the sanitized copy will be called,
* where it will be saved.

Safety rules enforced here, before the job is ever created:

* the destination can never resolve to the source file,
* the output always keeps the source file's format,
* an existing output is never silently replaced — the user must
  explicitly choose "new version" or "replace".

``ValidationService`` still performs its own checks inside the
processing engine; this dialog exists so the user sees a friendly
inline message instead of an exception after the fact.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QFileDialog,
    QHBoxLayout,
    QLineEdit,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from deskx.core.config import SANITIZED_SUFFIX, get_managed_output_dir
from deskx.core.utils import (
    build_output_filename,
    humanize_bytes,
    next_available_path,
    targets_same_file,
    truncate_path,
)
from deskx.gui.theme import SIZE, SPACE, palette
from deskx.gui.theme.icons import Icon, icon_label
from deskx.gui.widgets.components import (
    Button,
    Card,
    ChipButton,
    InfoNote,
    label,
)
from deskx.gui.widgets.modal import ModalDialog

_SETTINGS_ORG = "DeskX"
_SETTINGS_APP = "DataSanitizer"
_LAST_DIR_KEY = "output/last_directory"

# Characters Windows forbids in a file name.
_ILLEGAL_CHARS = set('<>:"/\\|?*')


@dataclass(frozen=True)
class SaveDestination:
    """The confirmed answer from the dialog."""

    output_path: Path
    directory: Path
    filename: str
    replaced_existing: bool
    save_pipeline: bool


class SaveDestinationDialog(ModalDialog):
    """Ask the user where the sanitized copy should be written."""

    def __init__(
        self,
        source_path: Path,
        pipeline_step_count: int = 0,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            title="Save processed file",
            subtitle="Choose where DeskX should save the sanitized copy.",
            icon=Icon.DOWNLOAD,
            width=620,
            primary_text="Process && Save",
            parent=parent,
        )
        self._source = Path(source_path)
        self._suffix = self._source.suffix
        self._pipeline_step_count = max(0, pipeline_step_count)
        # True while the chosen name collides with an existing file.
        self._conflict_active = False

        self._build_source_card()
        self._build_filename_field()
        self._build_location_field()
        self._build_conflict_section()
        self._build_pipeline_option()

        self._validation = InfoNote(
            "Your original file will remain unchanged.",
            variant="info",
            icon=Icon.SHIELD,
        )
        self.content.addWidget(self._validation)
        self.content.addStretch()

        self._filename_edit.setText(
            build_output_filename(self._source, SANITIZED_SUFFIX)
        )
        self._location_edit.setText(str(self._initial_directory()))

        self._filename_edit.textChanged.connect(self._revalidate)
        self._location_edit.textChanged.connect(self._revalidate)
        self._revalidate()

    # ── Result ──────────────────────────────────────────────────────

    def destination(self) -> SaveDestination | None:
        """Return the confirmed destination, or ``None`` if invalid."""
        resolved = self._resolved_path()
        if resolved is None:
            return None
        return SaveDestination(
            output_path=resolved,
            directory=resolved.parent,
            filename=resolved.name,
            replaced_existing=self._conflict_active
            and self._replace_radio.isChecked(),
            save_pipeline=self._save_pipeline_check.isChecked(),
        )

    # ── Construction ────────────────────────────────────────────────

    def _build_source_card(self) -> None:
        self.content.addWidget(label("SOURCE", "eyebrow"))

        card = Card(padding=SPACE.md, spacing=SPACE.xxs, variant="inset")
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(SPACE.md)
        row.addWidget(
            icon_label(_format_icon(self._suffix), palette().primary, SIZE.icon_xl),
            0,
            Qt.AlignmentFlag.AlignVCenter,
        )

        text_col = QVBoxLayout()
        text_col.setContentsMargins(0, 0, 0, 0)
        text_col.setSpacing(1)
        name = label(self._source.name, "cardTitle")
        name.setToolTip(str(self._source))
        text_col.addWidget(name)
        text_col.addWidget(label(self._source_details(), "caption"))
        row.addLayout(text_col, 1)

        card.add_layout(row)
        self.content.addWidget(card)

    def _source_details(self) -> str:
        parts = [truncate_path(self._source.parent, 52)]
        try:
            parts.append(humanize_bytes(self._source.stat().st_size))
        except OSError:
            pass
        return "   ·   ".join(parts)

    def _build_pipeline_option(self) -> None:
        """Offer to keep a reusable JSON copy of the configured steps."""
        card = Card(padding=SPACE.md, spacing=SPACE.xxs, variant="inset")
        self._save_pipeline_check = QCheckBox("Save pipeline configuration")
        self._save_pipeline_check.setChecked(False)
        self._save_pipeline_check.setEnabled(self._pipeline_step_count > 0)
        card.add(self._save_pipeline_check)

        if self._pipeline_step_count:
            detail = (
                f"Save {self._pipeline_step_count} transformation"
                f"{'' if self._pipeline_step_count == 1 else 's'} as JSON beside "
                "the processed file."
            )
        else:
            detail = "Add at least one transformation to save a pipeline."
        card.add(label(detail, "caption", wrap=True))
        self.content.addWidget(card)

    def _build_filename_field(self) -> None:
        self.content.addSpacing(SPACE.xs)
        self.content.addWidget(label("OUTPUT FILE NAME", "eyebrow"))

        self._filename_edit = QLineEdit()
        self._filename_edit.setMinimumHeight(SIZE.control_height_lg)
        self._filename_edit.setClearButtonEnabled(False)
        self._filename_edit.setToolTip(
            "The sanitized copy is written under this name. "
            f"The {self._suffix} format is always preserved."
        )
        self.content.addWidget(self._filename_edit)

    def _build_location_field(self) -> None:
        self.content.addSpacing(SPACE.xs)
        self.content.addWidget(label("SAVE LOCATION", "eyebrow"))

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(SPACE.sm)

        self._location_edit = QLineEdit()
        self._location_edit.setMinimumHeight(SIZE.control_height_lg)
        self._location_edit.setPlaceholderText("Choose a folder…")
        row.addWidget(self._location_edit, 1)

        browse = Button("Browse", icon=Icon.FOLDER_OPEN, height=SIZE.control_height_lg)
        browse.clicked.connect(self._on_browse)
        row.addWidget(browse)

        self.content.addLayout(row)

        chips = QHBoxLayout()
        chips.setContentsMargins(0, 0, 0, 0)
        chips.setSpacing(SPACE.sm)

        self._chip_source = ChipButton("Source folder", Icon.FOLDER)
        self._chip_source.setToolTip(f"Save next to the original: {self._source.parent}")
        self._chip_source.clicked.connect(
            lambda: self._location_edit.setText(str(self._source.parent))
        )
        chips.addWidget(self._chip_source)

        self._chip_managed = ChipButton("DeskX Output folder", Icon.DOWNLOAD)
        self._chip_managed.setToolTip(str(get_managed_output_dir()))
        self._chip_managed.clicked.connect(self._use_managed_folder)
        chips.addWidget(self._chip_managed)

        chips.addStretch()
        self.content.addLayout(chips)

    def _build_conflict_section(self) -> None:
        self._conflict_card = Card(padding=SPACE.md, spacing=SPACE.sm, variant="inset")

        head = QHBoxLayout()
        head.setContentsMargins(0, 0, 0, 0)
        head.setSpacing(SPACE.sm)
        head.addWidget(icon_label(Icon.WARNING, palette().warning, SIZE.icon_md))
        head.addWidget(label("A file with this name already exists", "caption", tone="warning"))
        head.addStretch()
        self._conflict_card.add_layout(head)

        self._conflict_group = QButtonGroup(self)

        self._version_radio = QRadioButton("Save as a new version")
        self._version_radio.setChecked(True)
        self._version_radio.setToolTip("Keeps the existing file and adds a numbered copy")
        self._conflict_group.addButton(self._version_radio, 0)
        self._conflict_card.add(self._version_radio)

        self._version_hint = label("", "caption")
        self._version_hint.setContentsMargins(24, 0, 0, 0)
        self._conflict_card.add(self._version_hint)

        self._replace_radio = QRadioButton("Replace the existing file")
        self._replace_radio.setToolTip("The current file at this location will be overwritten")
        self._conflict_group.addButton(self._replace_radio, 1)
        self._conflict_card.add(self._replace_radio)

        self._conflict_group.buttonClicked.connect(lambda _: self._revalidate())
        self._conflict_card.setVisible(False)
        self.content.addWidget(self._conflict_card)

    # ── Slots ───────────────────────────────────────────────────────

    def _on_browse(self) -> None:
        start = self._location_edit.text().strip() or str(self._source.parent)
        chosen = QFileDialog.getExistingDirectory(
            self,
            "Choose a folder for the sanitized copy",
            start,
            QFileDialog.Option.ShowDirsOnly,
        )
        if chosen:
            self._location_edit.setText(str(Path(chosen)))

    def _use_managed_folder(self) -> None:
        # Created on demand so the folder only appears once it is wanted.
        self._location_edit.setText(str(get_managed_output_dir(create=True)))

    # ── Validation ──────────────────────────────────────────────────

    def _revalidate(self) -> None:
        self._sync_chips()

        problem = self._first_problem()
        if problem is not None:
            self._show_problem(*problem)
            return

        target = self._target_path()
        assert target is not None  # guaranteed by _first_problem passing

        if target.exists():
            self._conflict_active = True
            self._conflict_card.setVisible(True)
            versioned = next_available_path(target)
            self._version_hint.setText(f"Saves as  {versioned.name}")
            if self._replace_radio.isChecked():
                self._set_state(
                    True,
                    f"“{target.name}” will be replaced. Your source file stays untouched.",
                    "warning",
                )
            else:
                self._set_state(
                    True,
                    "A new version will be created. Nothing existing is overwritten.",
                    "info",
                )
            return

        self._conflict_active = False
        self._conflict_card.setVisible(False)
        self._set_state(True, "Your original file will remain unchanged.", "info")

    def _first_problem(self) -> tuple[str, str] | None:
        """Return the first blocking (message, variant), or ``None``."""
        filename = self._filename_edit.text().strip()
        directory = self._location_edit.text().strip()

        if not filename:
            return ("Enter a name for the sanitized copy.", "error")

        if any(char in _ILLEGAL_CHARS for char in filename):
            return (
                'A file name cannot contain  <  >  :  "  /  \\  |  ?  *',
                "error",
            )

        typed_suffix = Path(filename).suffix
        if typed_suffix and typed_suffix.lower() != self._suffix.lower():
            return (
                f"Keep the {self._suffix} format — DeskX saves the copy in the "
                f"same format as the original.",
                "error",
            )

        if not directory:
            return ("Choose a folder to save into.", "error")

        folder = Path(directory)
        if not folder.is_dir():
            return ("That folder doesn't exist. Pick another one.", "error")

        if not os.access(folder, os.W_OK):
            return ("DeskX can't write to that folder. Pick another one.", "error")

        target = self._target_path()
        if target is None:
            return ("Choose a valid file name and folder.", "error")

        if targets_same_file(target, self._source):
            return (
                "That would overwrite your original file. "
                "Change the name or choose another folder.",
                "error",
            )

        return None

    def _target_path(self) -> Path | None:
        """The literal path the user typed, before conflict resolution."""
        filename = self._filename_edit.text().strip()
        directory = self._location_edit.text().strip()
        if not filename or not directory:
            return None
        if not Path(filename).suffix:
            filename = f"{filename}{self._suffix}"
        try:
            return Path(directory) / filename
        except (OSError, ValueError):
            return None

    def _resolved_path(self) -> Path | None:
        """The path DeskX will actually write, honouring the conflict choice."""
        if self._first_problem() is not None:
            return None
        target = self._target_path()
        if target is None:
            return None
        if target.exists() and self._version_radio.isChecked():
            return next_available_path(target)
        return target

    def _show_problem(self, message: str, variant: str) -> None:
        self._conflict_active = False
        self._conflict_card.setVisible(False)
        self._set_state(False, message, variant)

    def _set_state(self, valid: bool, message: str, variant: str) -> None:
        self._validation.set_message(message, variant)
        self.set_primary_enabled(valid)
        self._filename_edit.setProperty(
            "invalid", "true" if not valid and variant == "error" else "false"
        )
        from deskx.gui.theme.stylesheet import repolish

        repolish(self._filename_edit)

    def _sync_chips(self) -> None:
        current = self._location_edit.text().strip()
        for chip, folder in (
            (self._chip_source, self._source.parent),
            (self._chip_managed, get_managed_output_dir()),
        ):
            match = bool(current) and targets_same_file(Path(current), folder)
            if chip.isChecked() != match:
                chip.blockSignals(True)
                chip.setChecked(match)
                chip.blockSignals(False)
                chip._on_toggled(match)

    # ── Defaults & persistence ──────────────────────────────────────

    def _initial_directory(self) -> Path:
        """Prefer the last folder the user chose, else the source folder."""
        settings = QSettings(_SETTINGS_ORG, _SETTINGS_APP)
        remembered = settings.value(_LAST_DIR_KEY, "", type=str)
        if remembered:
            candidate = Path(remembered)
            if candidate.is_dir():
                return candidate
        return self._source.parent

    def _remember_directory(self, directory: Path) -> None:
        QSettings(_SETTINGS_ORG, _SETTINGS_APP).setValue(
            _LAST_DIR_KEY, str(directory)
        )

    # ── ModalDialog hook ────────────────────────────────────────────

    def _on_primary(self) -> None:
        self._revalidate()
        destination = self.destination()
        if destination is None:
            return
        if destination.directory == get_managed_output_dir():
            get_managed_output_dir(create=True)
        self._remember_directory(destination.directory)
        self.accept()


def _format_icon(suffix: str) -> str:
    """Pick an icon that matches the source file format."""
    return {
        ".xlsx": Icon.SPREADSHEET,
        ".csv": Icon.TABLE,
        ".json": Icon.DATABASE,
        ".txt": Icon.FILE,
    }.get(suffix.lower(), Icon.FILE)
