"""Pure, stateless helper functions.

Every function here must be free of side-effects and depend only on the
Python standard library.  No DeskX imports, no PySide6.
"""

from __future__ import annotations

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
