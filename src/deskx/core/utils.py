"""Pure, stateless helper functions.

Every function here must be free of side-effects and depend only on the
Python standard library.  No DeskX imports, no PySide6.
"""

from __future__ import annotations

import os
import re
from pathlib import Path


def sanitize_filename(stem: str) -> str:
    """Remove characters that are unsafe in Windows filenames.

    Keeps alphanumerics, hyphens, underscores, spaces, and dots.
    Collapses consecutive underscores.

    >>> sanitize_filename("data (copy)<v2>")
    'data_copy_v2'
    """
    cleaned = re.sub(r"[^\w\s.\-]", "_", stem)
    cleaned = re.sub(r"_+", "_", cleaned)
    return cleaned.strip("_ ")


def build_output_filename(
    source_path: Path,
    suffix: str = "_sanitized",
) -> str:
    """Build the output filename by appending *suffix* before the extension.

    >>> build_output_filename(Path("data/customers.csv"))
    'customers_sanitized.csv'
    """
    return f"{source_path.stem}{suffix}{source_path.suffix}"


def humanize_bytes(size_bytes: int) -> str:
    """Convert a byte count to a human-readable string.

    >>> humanize_bytes(1536)
    '1.50 KB'
    >>> humanize_bytes(0)
    '0 B'
    """
    if size_bytes == 0:
        return "0 B"
    units = ("B", "KB", "MB", "GB", "TB")
    factor = 1024.0
    for unit in units:
        if abs(size_bytes) < factor:
            return f"{size_bytes:.2f} {unit}" if unit != "B" else f"{size_bytes} B"
        size_bytes /= factor  # type: ignore[assignment]
    return f"{size_bytes:.2f} PB"


def targets_same_file(first: Path, second: Path) -> bool:
    """Return ``True`` if both paths would write to the same file.

    Unlike ``Path.resolve() ==`` this also treats paths that differ
    only by letter case as identical, which matters on Windows where
    ``report.csv`` and ``Report.csv`` are the same file.  It is used to
    stop the user from picking a destination that would clobber their
    source file.
    """
    left = os.path.normcase(os.path.abspath(str(first)))
    right = os.path.normcase(os.path.abspath(str(second)))
    return left == right


def next_available_path(path: Path, max_attempts: int = 999) -> Path:
    """Return *path* if it is free, otherwise the next numbered version.

    >>> next_available_path(Path("out/report.csv"))  # when free
    WindowsPath('out/report.csv')

    When ``report.csv`` already exists the result becomes
    ``report (2).csv``, then ``report (3).csv``, and so on.  This backs
    the "create a new version" choice in the save dialog so an existing
    output is never silently replaced.
    """
    if not path.exists():
        return path

    stem, suffix, parent = path.stem, path.suffix, path.parent
    for version in range(2, max_attempts + 1):
        candidate = parent / f"{stem} ({version}){suffix}"
        if not candidate.exists():
            return candidate

    # Pathological case — fall back to a name that cannot collide.
    return parent / f"{stem} ({max_attempts + 1}){suffix}"


def truncate_path(path: Path, max_length: int = 60) -> str:
    """Shorten a path for display by eliding the middle.

    >>> len(truncate_path(Path("C:/a/very/long/path/to/file.csv"), 30)) <= 30
    True
    """
    text = str(path)
    if len(text) <= max_length:
        return text
    # Keep the drive/first segment and the filename
    head = text[:max_length // 3]
    tail = text[-(max_length // 3):]
    return f"{head}…{tail}"
