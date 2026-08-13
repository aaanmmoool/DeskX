"""Application-wide configuration constants and paths.

This module is the single source of truth for magic strings, supported
file extensions, default limits, and platform-specific paths.  Nothing
here imports from any other DeskX module so it can be used everywhere.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Final

# ── Application identity ────────────────────────────────────────────
APP_NAME: Final[str] = "DeskX"
APP_VERSION: Final[str] = "0.1.0"
APP_DISPLAY_NAME: Final[str] = "DeskX — Data Transformation Tool"

# ── Supported file formats ──────────────────────────────────────────
SUPPORTED_EXTENSIONS: Final[frozenset[str]] = frozenset({
    ".csv", ".xlsx", ".json", ".txt",
})

FILE_FILTER_STRING: Final[str] = (
    "All Supported Files (*.csv *.xlsx *.json *.txt);;"
    "CSV Files (*.csv);;"
    "Excel Files (*.xlsx);;"
    "JSON Files (*.json);;"
    "Text Files (*.txt)"
)

# ── Preview limits ──────────────────────────────────────────────────
MAX_PREVIEW_ROWS: Final[int] = 200

# ── Recent-files history ────────────────────────────────────────────
MAX_RECENT_FILES: Final[int] = 10

# ── Hashing ─────────────────────────────────────────────────────────
HASH_ALGORITHM: Final[str] = "sha256"
HASH_BUFFER_SIZE: Final[int] = 8 * 1024 * 1024  # 8 MiB read chunks

# ── Output naming ───────────────────────────────────────────────────
SANITIZED_SUFFIX: Final[str] = "_sanitized"

# Folder offered as the managed alternative to "same folder as source".
OUTPUT_DIR_NAME: Final[str] = "Output"

# ── Temporary-file prefix ──────────────────────────────────────────
TEMP_FILE_PREFIX: Final[str] = ".deskx_tmp_"

# ── Platform paths ──────────────────────────────────────────────────
def get_app_data_dir() -> Path:
    """Return the per-user application data directory.

    On Windows this resolves to ``%APPDATA%/DeskX``.
    On other platforms it falls back to ``~/.deskx``.
    """
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", Path.home()))
    else:
        base = Path.home() / ".config"
    app_dir = base / APP_NAME
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir


def get_recent_files_path() -> Path:
    """Return the path to the recent-files JSON store."""
    return get_app_data_dir() / "recent_files.json"


def get_documents_dir() -> Path:
    """Return the user's Documents folder, falling back to the home dir."""
    if os.name == "nt":
        documents = Path.home() / "Documents"
        if documents.is_dir():
            return documents
    return Path.home()


def get_managed_output_dir(create: bool = False) -> Path:
    """Return the DeskX-managed output folder (``Documents/DeskX/Output``).

    This is offered alongside "same folder as the source file" in the
    save dialog.  The directory is only created when *create* is true,
    so merely displaying the path has no side effects.
    """
    output_dir = get_documents_dir() / APP_NAME / OUTPUT_DIR_NAME
    if create:
        output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir
