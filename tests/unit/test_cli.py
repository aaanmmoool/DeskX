"""CLI smoke tests — thin wrappers over existing DeskX services."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from deskx.cli.main import app
from deskx.core.config import APP_VERSION
from deskx.history.saved_pipeline import save_pipeline
from deskx.processing.pipeline import TransformStep, TransformType

runner = CliRunner()


@pytest.fixture
def sample_csv(tmp_path: Path) -> Path:
    path = tmp_path / "customers.csv"
    path.write_text(
        "id,email,name\n1,a@example.com,Ada\n2,b@example.com,Bob\n3,c@example.com,Cara\n",
        encoding="utf-8",
    )
    return path


@pytest.fixture
def sample_pipeline(tmp_path: Path) -> Path:
    steps = [
        TransformStep(TransformType.TRIM_WHITESPACE),
        TransformStep(TransformType.MASK_COLUMN, params={"column": "email"}),
    ]
    return save_pipeline(steps, tmp_path / "customers_sanitized.csv", name="PII Sanitization")


def test_root_help_lists_commands():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "preview" in result.stdout
    assert "transform" in result.stdout
    assert "pipeline" in result.stdout
    assert "version" in result.stdout


def test_version_flag_and_command():
    flagged = runner.invoke(app, ["--version"])
    commanded = runner.invoke(app, ["version"])
    assert flagged.exit_code == 0
    assert commanded.exit_code == 0
    assert APP_VERSION in flagged.stdout
    assert APP_VERSION in commanded.stdout


def test_preview_missing_file_message():
    result = runner.invoke(app, ["preview", r"C:\definitely\missing\file.csv"])
    assert result.exit_code == 2
    assert "not found" in (result.stdout + result.stderr).lower()


def test_preview_strips_extra_quotes(sample_csv: Path):
    quoted = f'"{sample_csv}"'
    result = runner.invoke(app, ["preview", quoted, "--rows", "1"])
    assert result.exit_code == 0
    assert "customers.csv" in result.stdout


def test_preview_shows_columns_and_rows(sample_csv: Path):
    result = runner.invoke(app, ["preview", str(sample_csv), "--rows", "2"])
    assert result.exit_code == 0
    assert "customers.csv" in result.stdout
    assert "email" in result.stdout
    assert "Ada" in result.stdout
    assert "Cara" not in result.stdout  # only first 2 rows


def test_pipeline_list_show_validate(sample_pipeline: Path, tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    listed = runner.invoke(app, ["pipeline", "list"])
    assert listed.exit_code == 0
    assert "PII Sanitization" in listed.stdout

    shown = runner.invoke(app, ["pipeline", "show", "PII Sanitization"])
    assert shown.exit_code == 0
    assert "Mask Email" in shown.stdout or "MASK_COLUMN" in shown.stdout or "Mask" in shown.stdout
    assert "email" in shown.stdout

    validated = runner.invoke(app, ["pipeline", "validate", str(sample_pipeline)])
    assert validated.exit_code == 0
    assert "valid" in validated.stdout.lower()


def test_pipeline_validate_rejects_bad_file(tmp_path: Path):
    bad = tmp_path / "broken_pipeline.json"
    bad.write_text(json.dumps({"steps": [{"transform_type": "NOPE"}]}), encoding="utf-8")
    result = runner.invoke(app, ["pipeline", "validate", str(bad)])
    assert result.exit_code == 1
    assert "invalid" in result.stdout.lower()


def test_transform_runs_existing_engine(
    sample_csv: Path, sample_pipeline: Path, tmp_path: Path
):
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    result = runner.invoke(
        app,
        [
            "transform",
            str(sample_csv),
            "--pipeline",
            str(sample_pipeline),
            "--output",
            str(out_dir),
        ],
    )
    assert result.exit_code == 0, result.stdout + result.stderr
    assert "Completed successfully" in result.stdout
    outputs = list(out_dir.glob("customers_sanitized*.csv"))
    assert outputs
    text = outputs[0].read_text(encoding="utf-8")
    assert "a@example.com" not in text
    assert "email" in text


def test_transform_refuses_source_overwrite(sample_csv: Path, sample_pipeline: Path):
    result = runner.invoke(
        app,
        [
            "transform",
            str(sample_csv),
            "--pipeline",
            str(sample_pipeline),
            "--output",
            str(sample_csv),
        ],
    )
    assert result.exit_code == 2
    assert "must differ" in (result.stdout + result.stderr).lower() or "same" in (
        result.stdout + result.stderr
    ).lower()
