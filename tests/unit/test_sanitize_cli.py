"""Tests for the interactive ``deskx sanitize`` workflow."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
from typer.testing import CliRunner

from deskx.cli._sanitize_core import (
    ColumnChoice,
    choices_to_steps,
    confidence_label,
    default_params,
    synthetic_example,
)
from deskx.cli.main import app
from deskx.cli.sanitize import Cancelled, run_sanitize_workflow
from deskx.processing.pipeline import TransformType

runner = CliRunner()


@pytest.fixture
def sample_csv(tmp_path: Path) -> Path:
    path = tmp_path / "customers.csv"
    path.write_text(
        "id,email,phone,city\n"
        "1,ada@example.com,555-0100,London\n"
        "2,bob@example.com,555-0101,Paris\n"
        "3,cara@example.com,555-0102,Berlin\n",
        encoding="utf-8",
    )
    return path


@pytest.fixture
def sample_json(tmp_path: Path) -> Path:
    path = tmp_path / "people.json"
    path.write_text(
        '[{"email":"a@example.com","name":"Ada"},'
        '{"email":"b@example.com","name":"Bob"}]\n',
        encoding="utf-8",
    )
    return path


class ScriptedAsk:
    """Feed predetermined answers to the interactive prompts."""

    def __init__(self, answers: list[str]) -> None:
        self._answers = list(answers)
        self.seen: list[str] = []

    def __call__(self, prompt: str) -> str:
        self.seen.append(prompt)
        if not self._answers:
            raise AssertionError(f"No scripted answer left for prompt: {prompt!r}")
        return self._answers.pop(0)


def test_sanitize_help_lists_options():
    result = runner.invoke(app, ["sanitize", "--help"])
    assert result.exit_code == 0
    assert "--output" in result.stdout
    assert "sensitive" in result.stdout.lower() or "sanitize" in result.stdout.lower()


def test_root_help_includes_sanitize():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "sanitize" in result.stdout


def test_sanitize_missing_file():
    result = runner.invoke(app, ["sanitize", r"C:\missing\file.csv"])
    assert result.exit_code == 2
    assert "not found" in (result.stdout + result.stderr).lower()


def test_sanitize_unsupported_format(tmp_path: Path):
    path = tmp_path / "notes.pdf"
    path.write_bytes(b"%PDF")
    result = runner.invoke(app, ["sanitize", str(path)])
    assert result.exit_code == 2
    assert "unsupported" in (result.stdout + result.stderr).lower()


def test_confidence_and_examples_are_safe():
    assert confidence_label(0.9) == "High"
    before, after = synthetic_example(
        TransformType.MASK_COLUMN, "email", {"show_last": 4}
    )
    assert before == "john.doe@example.com"
    assert after.endswith("com")
    assert "ada@" not in after


def test_choices_to_steps_builds_engine_params():
    choice = ColumnChoice(
        column="email",
        category="email",
        action_label="Mask",
        transform_type=TransformType.MASK_COLUMN,
        params=default_params(TransformType.MASK_COLUMN, "email"),
    )
    steps = choices_to_steps({"email": choice})
    assert len(steps) == 1
    assert steps[0].params["column"] == "email"
    assert steps[0].params["show_last"] == 4


def test_interactive_sanitize_same_folder_and_pipeline(sample_csv: Path, tmp_path: Path):
    ask = ScriptedAsk(
        [
            "1",  # select email
            "1",  # mask
            "1",  # show last 4
            "y",  # apply
            "2",  # select phone
            "3",  # hash
            "y",  # apply
            "d",  # done
            "y",  # review continue
            "y",  # same folder
            "y",  # save pipeline
            "PII Sanitization",
        ]
    )
    messages: list[str] = []

    output = run_sanitize_workflow(
        file=str(sample_csv),
        ask=ask,
        echo=messages.append,
    )

    assert output.exists()
    assert output.parent == sample_csv.parent
    assert "sanitized" in output.name
    assert output != sample_csv

    text = output.read_text(encoding="utf-8")
    assert "ada@example.com" not in text
    assert "555-0100" not in text
    assert "email" in text

    pipelines = list(sample_csv.parent.glob("*_pipeline*.json"))
    assert pipelines
    assert "PII Sanitization" in pipelines[0].read_text(encoding="utf-8")


def test_interactive_sanitize_other_folder_and_output_option(
    sample_csv: Path, tmp_path: Path
):
    other = tmp_path / "elsewhere"
    ask = ScriptedAsk(
        [
            "1",
            "2",  # redact
            "HIDDEN",
            "y",
            "d",
            "y",
            "o",
            str(other),
            "n",  # do not save pipeline
        ]
    )
    output = run_sanitize_workflow(file=str(sample_csv), ask=ask, echo=lambda *_: None)
    assert output.parent == other
    assert "HIDDEN" in output.read_text(encoding="utf-8")

    forced = tmp_path / "forced"
    ask2 = ScriptedAsk(
        [
            "1",
            "5",  # remove
            "y",
            "d",
            "y",
            "n",
        ]
    )
    output2 = run_sanitize_workflow(
        file=str(sample_csv),
        output=str(forced),
        ask=ask2,
        echo=lambda *_: None,
    )
    assert output2.parent == forced
    frame = pd.read_csv(output2)
    assert "email" not in frame.columns


def test_sanitize_cancel(sample_csv: Path):
    ask = ScriptedAsk(["q"])
    with pytest.raises(Cancelled):
        run_sanitize_workflow(file=str(sample_csv), ask=ask, echo=lambda *_: None)


def test_sanitize_refuses_source_overwrite(sample_csv: Path):
    ask = ScriptedAsk(
        [
            "1",
            "1",
            "1",
            "y",
            "d",
            "y",
            "n",
        ]
    )
    with pytest.raises(Exception):
        run_sanitize_workflow(
            file=str(sample_csv),
            output=str(sample_csv),
            ask=ask,
            echo=lambda *_: None,
        )


def test_sanitize_json(sample_json: Path, tmp_path: Path):
    ask = ScriptedAsk(
        [
            "1",
            "1",
            "1",
            "y",
            "d",
            "y",
            "n",
        ]
    )
    output = run_sanitize_workflow(
        file=str(sample_json),
        output=str(tmp_path / "out"),
        ask=ask,
        echo=lambda *_: None,
    )
    assert output.suffix == ".json"
    assert "a@example.com" not in output.read_text(encoding="utf-8")


def test_guess_header_row_for_titled_xlsx(tmp_path: Path):
    from openpyxl import Workbook

    from deskx.adapters.adapter_registry import create_default_registry
    from deskx.cli._import_options import guess_header_row

    path = tmp_path / "titled.xlsx"
    wb = Workbook()
    ws = wb.active
    ws.append([None, "Report Title"])
    ws.append([])
    ws.append([None, "Email", "Phone", "City"])
    ws.append([None, "a@example.com", "555-0100", "London"])
    wb.save(path)

    guessed = guess_header_row(path, registry=create_default_registry())
    assert guessed == 2


def test_existing_output_gets_versioned(sample_csv: Path, tmp_path: Path):
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    existing = out_dir / "customers_sanitized.csv"
    existing.write_text("old", encoding="utf-8")

    ask = ScriptedAsk(
        [
            "1",
            "3",  # hash
            "y",
            "d",
            "y",
            "n",
        ]
    )
    output = run_sanitize_workflow(
        file=str(sample_csv),
        output=str(out_dir),
        ask=ask,
        echo=lambda *_: None,
    )
    assert output.name == "customers_sanitized (2).csv"
    assert existing.read_text(encoding="utf-8") == "old"
