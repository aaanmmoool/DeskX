"""JSON-backed Most-Recently-Used (MRU) file list.

Stores up to :data:`~deskx.core.config.MAX_RECENT_FILES` entries in a
JSON file under the user's application data directory.  Each entry
records the absolute file path and the ISO-8601 timestamp of last
access.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from deskx.core.config import MAX_RECENT_FILES, get_recent_files_path

logger = logging.getLogger(__name__)


@dataclass
class RecentEntry:
    """A single entry in the recent-files list."""

    path: str
    last_opened: str  # ISO-8601

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RecentEntry:
        return cls(path=data["path"], last_opened=data["last_opened"])


class RecentFilesManager:
    """Manages the persisted recent-files list.

    Parameters
    ----------
    storage_path
        Path to the JSON file.  Defaults to the platform-specific
        app-data location.
    max_entries
        Maximum number of entries to retain.
    """

    def __init__(
        self,
        storage_path: Path | None = None,
        max_entries: int = MAX_RECENT_FILES,
    ) -> None:
        self._storage_path = storage_path or get_recent_files_path()
        self._max = max_entries
        self._entries: list[RecentEntry] = []
        self._load()

    # ── Public API ──────────────────────────────────────────────────

    @property
    def entries(self) -> list[RecentEntry]:
        """Return a copy of the current entries (most-recent first)."""
        return list(self._entries)

    def add(self, file_path: Path) -> None:
        """Add or bump *file_path* to the top of the list."""
        resolved = str(file_path.resolve())
        # Remove existing entry for this path (if any)
        self._entries = [
            e for e in self._entries if e.path != resolved
        ]
        # Prepend new entry
        self._entries.insert(
            0,
            RecentEntry(
                path=resolved,
                last_opened=datetime.now(timezone.utc).isoformat(),
            ),
        )
        # Trim to max
        self._entries = self._entries[: self._max]
        self._save()

    def remove(self, file_path: Path) -> None:
        """Remove *file_path* from the list."""
        resolved = str(file_path.resolve())
        self._entries = [
            e for e in self._entries if e.path != resolved
        ]
        self._save()

    def clear(self) -> None:
        """Remove all entries."""
        self._entries.clear()
        self._save()

    # ── Persistence ─────────────────────────────────────────────────

    def _load(self) -> None:
        if not self._storage_path.exists():
            return
        try:
            data = json.loads(self._storage_path.read_text("utf-8"))
            self._entries = [
                RecentEntry.from_dict(item) for item in data
            ]
        except (json.JSONDecodeError, KeyError, TypeError):
            logger.warning(
                "Corrupt recent-files store at %s — resetting.",
                self._storage_path,
            )
            self._entries = []

    def _save(self) -> None:
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        payload = [e.to_dict() for e in self._entries]
        self._storage_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
