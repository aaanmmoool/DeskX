"""Adapter registry — maps file extensions to concrete adapters.

Adding a new format requires:

1. Create a new ``FileAdapter`` subclass.
2. Register it here with ``register()``.

The registry is pre-populated with the four built-in adapters on import.
"""

from __future__ import annotations

from deskx.adapters.csv_adapter import CsvAdapter
from deskx.adapters.json_adapter import JsonAdapter
from deskx.adapters.txt_adapter import TxtAdapter
from deskx.adapters.xlsx_adapter import XlsxAdapter
from deskx.core.exceptions import UnsupportedFormatError
from deskx.processing.interfaces import FileAdapter


class AdapterRegistry:
    """Extension → :class:`FileAdapter` lookup."""

    def __init__(self) -> None:
        self._adapters: dict[str, FileAdapter] = {}

    # ── Registration ────────────────────────────────────────────────

    def register(self, adapter: FileAdapter) -> None:
        """Register *adapter* for all of its declared extensions."""
        for ext in adapter.extensions:
            self._adapters[ext.lower()] = adapter

    # ── Lookup ──────────────────────────────────────────────────────

    def get(self, extension: str) -> FileAdapter:
        """Return the adapter for *extension*.

        Raises
        ------
        UnsupportedFormatError
            If no adapter is registered for the extension.
        """
        ext = extension.lower()
        if ext not in self._adapters:
            raise UnsupportedFormatError(ext)
        return self._adapters[ext]

    def is_supported(self, extension: str) -> bool:
        """Return ``True`` if *extension* has a registered adapter."""
        return extension.lower() in self._adapters

    @property
    def supported_extensions(self) -> frozenset[str]:
        """Return all registered extensions."""
        return frozenset(self._adapters.keys())


def create_default_registry() -> AdapterRegistry:
    """Build a registry pre-loaded with all built-in adapters."""
    registry = AdapterRegistry()
    registry.register(CsvAdapter())
    registry.register(JsonAdapter())
    registry.register(XlsxAdapter())
    registry.register(TxtAdapter())
    return registry
