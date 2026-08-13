"""Tests for portable transformation-pipeline persistence."""

from __future__ import annotations

import json
from pathlib import Path

from deskx.history.saved_pipeline import (
    PIPELINE_SCHEMA_VERSION,
    pipeline_path_for_output,
    pipeline_payload,
    save_pipeline,
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

    saved = save_pipeline(_steps(), output)
    document = json.loads(saved.read_text(encoding="utf-8"))

    assert saved == tmp_path / "customers_sanitized_pipeline.json"
    assert document["application"] == "DeskX"
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
