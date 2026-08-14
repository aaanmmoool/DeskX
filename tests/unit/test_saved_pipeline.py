"""Tests for portable transformation-pipeline persistence."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from deskx.history.saved_pipeline import (
    PIPELINE_SCHEMA_VERSION,
    PipelineLoadError,
    list_pipelines,
    load_pipeline,
    pipeline_path_for_output,
    pipeline_payload,
    resolve_pipeline,
    save_pipeline,
    validate_pipeline,
    validate_pipeline_document,
)
from deskx.processing.pipeline import TransformStep, TransformType


def _steps() -> list[TransformStep]:
    return [
        TransformStep(TransformType.TRIM_WHITESPACE),
        TransformStep(
            TransformType.MASK_COLUMN,
            params={"column": "email", "visible_chars": 2},
        ),
    ]


def test_payload_uses_stable_enum_names():
    payload = pipeline_payload(_steps())

    assert payload["schema_version"] == PIPELINE_SCHEMA_VERSION
    assert payload["steps"] == [
        {
            "transform_type": "TRIM_WHITESPACE",
            "enabled": True,
            "params": {},
        },
        {
            "transform_type": "MASK_COLUMN",
            "enabled": True,
            "params": {"column": "email", "visible_chars": 2},
        },
    ]


def test_pipeline_is_saved_beside_output(tmp_path: Path):
    output = tmp_path / "customers_sanitized.csv"
    output.write_text("id,email\n", encoding="utf-8")

    saved = save_pipeline(_steps(), output, name="PII Sanitization")
    document = json.loads(saved.read_text(encoding="utf-8"))

    assert saved == tmp_path / "customers_sanitized_pipeline.json"
    assert document["application"] == "DeskX"
    assert document["name"] == "PII Sanitization"
    assert len(document["steps"]) == 2


def test_existing_pipeline_is_never_overwritten(tmp_path: Path):
    output = tmp_path / "customers_sanitized.csv"
    first = tmp_path / "customers_sanitized_pipeline.json"
    first.write_text("keep me", encoding="utf-8")

    saved = save_pipeline(_steps(), output)

    assert saved == tmp_path / "customers_sanitized_pipeline (2).json"
    assert first.read_text(encoding="utf-8") == "keep me"


def test_path_helper_does_not_require_output_to_exist(tmp_path: Path):
    output = tmp_path / "result.xlsx"
    assert pipeline_path_for_output(output) == tmp_path / "result_pipeline.json"


def test_load_pipeline_round_trip(tmp_path: Path):
    output = tmp_path / "out.csv"
    path = save_pipeline(_steps(), output, name="Research Dataset")

    loaded = load_pipeline(path)

    assert loaded.name == "Research Dataset"
    assert len(loaded.steps) == 2
    assert loaded.steps[0].transform_type is TransformType.TRIM_WHITESPACE
    assert loaded.steps[1].params["column"] == "email"


def test_list_and_resolve_by_name(tmp_path: Path):
    path = save_pipeline(_steps(), tmp_path / "a.csv", name="Analytics Cleanup")

    found = list_pipelines([tmp_path])
    assert [item.name for item in found] == ["Analytics Cleanup"]

    resolved = resolve_pipeline("Analytics Cleanup", search_dirs=[tmp_path])
    assert resolved.path == path.resolve()


def test_validate_accepts_good_document():
    result = validate_pipeline_document(pipeline_payload(_steps()))
    assert result.ok


def test_validate_rejects_unknown_transform():
    document = pipeline_payload(_steps())
    document["steps"][0]["transform_type"] = "NOT_A_REAL_TRANSFORM"
    result = validate_pipeline_document(document)
    assert not result.ok
    assert any("unknown transform_type" in msg for msg in result.error_messages)


def test_validate_rejects_privacy_step_without_column():
    document = {
        "schema_version": 1,
        "steps": [{"transform_type": "MASK_COLUMN", "params": {}, "enabled": True}],
    }
    result = validate_pipeline_document(document)
    assert not result.ok
    assert any("requires a 'column'" in msg for msg in result.error_messages)


def test_validate_pipeline_file(tmp_path: Path):
    path = save_pipeline(_steps(), tmp_path / "x.csv")
    assert validate_pipeline(path).ok


def test_resolve_missing_pipeline_raises(tmp_path: Path):
    with pytest.raises(PipelineLoadError, match="No saved pipeline"):
        resolve_pipeline("Missing Pipeline", search_dirs=[tmp_path])
