"""Built-in user guide and privacy explainer.

Both dialogs are read-only reference material rendered with the shared
modal chrome, so they look and behave like every other DeskX dialog.
The wording explains what the app already does — no feature described
here is new.
"""

from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QTabWidget, QVBoxLayout, QWidget

from deskx.gui.theme import SPACE
from deskx.gui.theme.icons import Icon
from deskx.gui.widgets.components import (
    Badge,
    Card,
    InfoNote,
    SectionHeader,
    label,
    scroll_container,
)
from deskx.gui.widgets.modal import ModalDialog

_QUICK_START = (
    (
        Icon.UPLOAD,
        "1 · Choose a dataset",
        "Drag a file onto the upload area or press Browse. DeskX reads "
        "CSV, Excel, JSON, and delimited text files.",
    ),
    (
        Icon.PREVIEW,
        "2 · Check the preview",
        "Confirm DeskX is reading the file the way you expect — the "
        "header row, the worksheet, the separator — then page through "
        "the data or search it.",
    ),
    (
        Icon.TRANSFORM,
        "3 · Add transformations",
        "Pick rules from the catalog, or accept a suggestion for a "
        "column DeskX flagged as sensitive. Each rule opens a small "
        "dialog where you choose the columns and settings.",
    ),
    (
        Icon.PIPELINE,
        "4 · Review the pipeline",
        "The Review tab shows the whole run as a list: the file coming "
        "in, each step in order, and the file going out.",
    ),
    (
        Icon.DOWNLOAD,
        "5 · Choose where to save",
        "Before anything is written, DeskX asks for the output name and "
        "folder. It refuses to write over your source file, and never "
        "silently replaces an existing output.",
    ),
    (
        Icon.REPORTS,
        "6 · Keep the report",
        "Every run produces an audit report with SHA-256 hashes of both "
        "files and a summary of what was applied.",
    ),
)

_TRANSFORM_GROUPS = (
    (
        "Cleaning",
        Icon.CLEAN,
        (
            ("Trim whitespace", "Removes stray spaces around values and column titles."),
            ("Remove empty rows and columns", "Drops anything that is entirely blank."),
            ("Remove duplicates", "Keeps one copy of each repeated row."),
            ("Fill missing values", "Puts a value of your choice into blank cells."),
        ),
    ),
    (
        "Privacy",
        Icon.SHIELD,
        (
            ("Mask", "Hides most of a value but leaves it recognizable — j***@example.com."),
            ("Redact", "Replaces the value completely, so nothing is left to read."),
            ("Hash", "Replaces a value with a one-way fingerprint. Equal values stay equal; nothing can be read back."),
            ("Pseudonymize", "Swaps identifying values for consistent stand-in names or IDs."),
        ),
    ),
    (
        "Shaping",
        Icon.GENERALIZE,
        (
            ("Rename columns", "Gives columns clearer titles."),
            ("Reorder columns", "Moves the columns you care about to the front."),
            ("Group numbers into bands", "Turns exact figures into ranges such as Low or High."),
            ("Suppress rare values", "Folds categories that appear only a few times into “Other”."),
        ),
    ),
)

_SHORTCUTS = (
    ("Ctrl + O", "Open a dataset"),
    ("F1", "Open this guide"),
    ("Enter", "Confirm the highlighted action in a dialog"),
    ("Esc", "Close a dialog without changing anything"),
    ("Tab", "Move between controls"),
)


class HelpDialog(ModalDialog):
    """The built-in user guide."""

    def __init__(self, parent=None) -> None:
        super().__init__(
            title="User Guide",
            subtitle="How DeskX prepares your data, in plain language.",
            icon=Icon.HELP,
            width=720,
            primary_text="Got it",
            parent=parent,
        )
        self.setWindowTitle("DeskX — User Guide")
        self.cancel_button.setVisible(False)
        self.resize(720, 620)

        tabs = QTabWidget()
        tabs.setDocumentMode(True)
        tabs.addTab(self._build_quick_start(), "Quick start")
        tabs.addTab(self._build_transforms(), "Transformations")
        tabs.addTab(self._build_privacy(), "Privacy")
        tabs.addTab(self._build_shortcuts(), "Shortcuts")
        self.content.addWidget(tabs, 1)

    # ── Tabs ────────────────────────────────────────────────────────

    def _build_quick_start(self) -> QWidget:
        page, col = _tab_page()
        for icon, title, text in _QUICK_START:
            card = Card(padding=SPACE.md, spacing=SPACE.xs, variant="cardFlat")
            card.add(SectionHeader(title, icon))
            card.add(label(text, "body", wrap=True))
            col.addWidget(card)
        col.addStretch()
        return scroll_container(page)

    def _build_transforms(self) -> QWidget:
        page, col = _tab_page()
        col.addWidget(
            label(
                "Every rule runs on a copy of your data. Your source file "
                "is only ever read.",
                "body",
                wrap=True,
            )
        )
        for title, icon, entries in _TRANSFORM_GROUPS:
            card = Card(padding=SPACE.md, spacing=SPACE.sm, variant="cardFlat")
            card.add(SectionHeader(title, icon))
            for name, description in entries:
                card.add(label(name, "body"))
                hint = label(description, "caption", wrap=True)
                hint.setContentsMargins(SPACE.md, 0, 0, SPACE.xs)
                card.add(hint)
            col.addWidget(card)
        col.addStretch()
        return scroll_container(page)

    def _build_privacy(self) -> QWidget:
        page, col = _tab_page()
        col.addWidget(_privacy_body())
        col.addStretch()
        return scroll_container(page)

    def _build_shortcuts(self) -> QWidget:
        page, col = _tab_page()
        card = Card(padding=SPACE.lg, spacing=SPACE.sm, variant="cardFlat")
        card.add(SectionHeader("Keyboard", Icon.SETTINGS))
        for keys, description in _SHORTCUTS:
            row = QHBoxLayout()
            row.setSpacing(SPACE.md)
            chip = Badge(keys, "neutral")
            chip.setMinimumWidth(96)
            row.addWidget(chip)
            row.addWidget(label(description, "body"), 1)
            card.add_layout(row)
        col.addWidget(card)
        col.addStretch()
        return scroll_container(page)


class PrivacyDialog(ModalDialog):
    """A short explanation of how DeskX protects the user's data."""

    def __init__(self, parent=None) -> None:
        super().__init__(
            title="Privacy",
            subtitle="What DeskX does with your files — and what it never does.",
            icon=Icon.PRIVACY,
            width=620,
            primary_text="Close",
            parent=parent,
        )
        self.setWindowTitle("DeskX — Privacy")
        self.cancel_button.setVisible(False)
        self.content.addWidget(_privacy_body())
        self.content.addStretch()


# ── Shared content ──────────────────────────────────────────────────


def _privacy_body() -> QWidget:
    """The privacy explanation, shared by both dialogs."""
    holder = QWidget()
    col = QVBoxLayout(holder)
    col.setContentsMargins(0, 0, 0, 0)
    col.setSpacing(SPACE.md)

    col.addWidget(
        InfoNote(
            "DeskX makes no network requests. Your data never leaves this "
            "computer.",
            variant="success",
            icon=Icon.LOCK,
        )
    )

    protections = Card(padding=SPACE.md, spacing=SPACE.sm, variant="cardFlat")
    protections.add(SectionHeader("How your file is handled", Icon.SHIELD))
    for text in (
        "The source file is opened read-only and is never rewritten.",
        "Results are written to a temporary file first, then promoted only "
        "once every step has succeeded.",
        "A destination that would overwrite your source file is rejected "
        "before processing starts.",
        "Both files are SHA-256 hashed so you can prove afterwards which "
        "file produced which result.",
    ):
        protections.add(label(f"·   {text}", "body", wrap=True))
    col.addWidget(protections)

    detection = Card(padding=SPACE.md, spacing=SPACE.sm, variant="cardFlat")
    detection.add(
        SectionHeader(
            "Sensitive-column detection",
            Icon.SEARCH,
            "DeskX inspects column titles and sample values to flag data "
            "that usually needs protecting.",
        )
    )
    for text in (
        "Email addresses and phone numbers",
        "Names and employee identifiers",
        "Financial details such as card and account numbers",
        "Government identifiers and postal addresses",
    ):
        detection.add(label(f"·   {text}", "body", wrap=True))
    detection.add(
        label(
            "Detection is a suggestion, not a guarantee. Always review the "
            "flagged columns yourself.",
            "caption",
            wrap=True,
        )
    )
    col.addWidget(detection)

    return holder


def _tab_page() -> tuple[QWidget, QVBoxLayout]:
    """A padded, transparent page used inside the guide's tabs."""
    page = QWidget()
    page.setObjectName("pageRoot")
    col = QVBoxLayout(page)
    col.setContentsMargins(SPACE.lg, SPACE.lg, SPACE.lg, SPACE.lg)
    col.setSpacing(SPACE.md)
    return page, col
