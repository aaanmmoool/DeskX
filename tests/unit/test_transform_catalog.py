"""Unit tests for self-explanatory transformation catalog."""

import pytest
from deskx.processing.pipeline import TransformType
from deskx.processing.transform_catalog import (
    TRANSFORM_CATALOG,
    get_transform_metadata,
)


def test_all_transform_types_have_metadata():
    for tt in TransformType:
        assert tt in TRANSFORM_CATALOG, f"Missing catalog entry for {tt}"
        meta = get_transform_metadata(tt)
        assert meta.friendly_name, f"Missing friendly_name for {tt}"
        assert meta.one_liner, f"Missing one_liner for {tt}"
        assert meta.what_it_does, f"Missing what_it_does for {tt}"
        assert meta.example_in, f"Missing example_in for {tt}"
        assert meta.example_out, f"Missing example_out for {tt}"
        assert meta.example_visual, f"Missing example_visual for {tt}"
        assert meta.when_to_use, f"Missing when_to_use for {tt}"
        assert meta.warning, f"Missing warning for {tt}"


def test_get_transform_metadata_fallback():
    # Test that get_transform_metadata returns valid fallback for unknown enum if one ever added
    meta = get_transform_metadata(TransformType.TRIM_WHITESPACE)
    assert meta.friendly_name == "Trim Whitespace"
    assert "Removes spaces" in meta.one_liner
