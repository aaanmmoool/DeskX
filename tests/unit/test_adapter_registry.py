"""Tests for adapters.adapter_registry module."""

from __future__ import annotations

import pytest

from deskx.adapters.adapter_registry import (
    AdapterRegistry,
    create_default_registry,
)
from deskx.core.exceptions import UnsupportedFormatError


class TestAdapterRegistry:
    def test_default_registry_has_all_formats(self):
        reg = create_default_registry()
        assert reg.is_supported(".csv")
        assert reg.is_supported(".json")
        assert reg.is_supported(".xlsx")
        assert reg.is_supported(".txt")

    def test_get_returns_adapter(self):
        reg = create_default_registry()
        adapter = reg.get(".csv")
        assert adapter.display_name == "CSV"

    def test_get_case_insensitive(self):
        reg = create_default_registry()
        adapter = reg.get(".CSV")
        assert adapter.display_name == "CSV"

    def test_unsupported_extension_raises(self):
        reg = create_default_registry()
        with pytest.raises(UnsupportedFormatError):
            reg.get(".pdf")

    def test_supported_extensions_property(self):
        reg = create_default_registry()
        exts = reg.supported_extensions
        assert isinstance(exts, frozenset)
        assert len(exts) == 4

    def test_register_custom_adapter(self):
        from deskx.adapters.csv_adapter import CsvAdapter

        reg = AdapterRegistry()
        assert not reg.is_supported(".csv")
        reg.register(CsvAdapter())
        assert reg.is_supported(".csv")
