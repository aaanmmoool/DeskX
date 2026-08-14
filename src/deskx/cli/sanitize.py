"""``deskx sanitize`` — interactive sensitive-column sanitization.

Architecture::

    CLI prompts
        ↓
    detect_sensitive_columns  (existing)
        ↓
    TransformStep list
        ↓
    ProcessingJob            (existing)
        ↓
    adapters + report        (existing)

No transformation logic lives in this module.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Callable, Optional

import typer

from deskx.adapters.adapter_registry import create_default_registry
from deskx.cli import _terminal as term
from deskx.cli._import_options import resolve_import_kwargs
from deskx.cli._paths import resolve_existing_file, resolve_output_path
from deskx.cli._sanitize_core import (
    SANITIZE_ACTIONS,
    ColumnChoice,
    action_for_key,
    category_label,
    choices_to_steps,
    confidence_label,
    default_params,
    summarize_detection,
    synthetic_example,
)
from deskx.core.config import SANITIZED_SUFFIX
from deskx.core.exceptions import DeskXError, UnsupportedFormatError
from deskx.core.utils import build_output_filename, next_available_path, targets_same_file
from deskx.history.saved_pipeline import save_pipeline
from deskx.processing.job import JobConfig, JobStatus, ProcessingJob, ProgressUpdate
from deskx.processing.pipeline import TransformType
from deskx.processing.sensitive_detector import SensitiveColumn, detect_sensitive_columns
from deskx.processing.validation_service import ValidationService

AskFn = Callable[[str], str]
EchoFn = Callable[[str], None]

_STATUS_LABELS = {
    JobStatus.VALIDATING: "Validated paths",
    JobStatus.HASHING_SOURCE: "Hashed source file",
    JobStatus.READING: "Read dataset",
    JobStatus.PROCESSING: "Applied transformations",
    JobStatus.WRITING: "Wrote output",
    JobStatus.VALIDATING_OUTPUT: "Validated output",
    JobStatus.HASHING_OUTPUT: "Hashed output file",
    JobStatus.GENERATING_REPORT: "Generated report",
}


class Cancelled(Exception):
    """User cancelled the interactive workflow."""


def sanitize_command(
    file: Annotated[
        str,
        typer.Argument(help="Dataset to sanitize (CSV, XLSX, JSON, or TXT)."),
    ],
    output: Annotated[
        Optional[str],
        typer.Option(
            "--output",
            "-o",
            help="Output file or directory. Skips the save-location prompt.",
        ),
    ] = None,
    sheet: Annotated[
        Optional[str],
        typer.Option("--sheet", help="Worksheet name (XLSX only)."),
    ] = None,
    header_row: Annotated[
        Optional[int],
        typer.Option(
            "--header-row",
            help="1-based row number that contains column names "
            "(for spreadsheets with a title above the table).",
            min=1,
        ),
    ] = None,
    yes: Annotated[
        bool,
        typer.Option(
            "--yes",
            "-y",
            help="Accept the final review without an extra confirmation.",
        ),
    ] = False,
) -> None:
    """Interactively sanitize sensitive columns in a dataset.

    Runs the existing sensitive-data detector, lets you choose a
    transformation per column, then executes the same ProcessingJob
    used by the desktop app and ``deskx transform``.

    Examples:

        deskx sanitize customers.xlsx

        deskx sanitize customers.csv --output C:\\Sanitized

        deskx sanitize report.xlsx --header-row 6

    The original file is never modified.
    """
    try:
        run_sanitize_workflow(
            file=file,
            output=output,
            sheet=sheet,
            header_row=None if header_row is None else header_row - 1,
            auto_confirm=yes,
        )
    except Cancelled:
        term.bullet_fail("Cancelled — nothing was written")
        raise typer.Exit(code=1)
    except DeskXError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=2) from exc


def run_sanitize_workflow(
    *,
    file: str,
    output: str | None = None,
    sheet: str | None = None,
    header_row: int | None = None,
    auto_confirm: bool = False,
    ask: AskFn | None = None,
    echo: EchoFn | None = None,
) -> Path:
    """Run the sanitize workflow; returns the output path.

    *ask* / *echo* are injectable so unit tests can drive the prompts
    without a real TTY.  *header_row* is 0-based (pandas style).
    """
    ask = ask or _default_ask
    echo = echo or (lambda message: typer.echo(message))

    source = resolve_existing_file(file, label="Dataset")
    registry = create_default_registry()
    try:
        adapter = registry.get(source.suffix)
    except UnsupportedFormatError as exc:
        raise DeskXError(str(exc)) from exc

    try:
        kwargs = resolve_import_kwargs(
            source,
            registry=registry,
            sheet=sheet,
            header_row=header_row,
        )
    except ValueError as exc:
        raise DeskXError(str(exc)) from exc

    # Bounded read for detection only — ProcessingJob loads the full file later.
    sample = adapter.read_preview(source, max_rows=500, **kwargs)
    # Drop fully empty / leftover index columns from title-banner sheets.
    sample = sample.dropna(axis=1, how="all")
    sample = sample.loc[:, [c for c in sample.columns if not str(c).startswith("Unnamed")]]
    detected = detect_sensitive_columns(sample)

    echo("DeskX - Sensitive Data Sanitizer")
    term.rule()
    echo("")
    echo("File:")
    echo(str(source))
    echo(f"Header row: {int(kwargs.get('header_row', 0)) + 1}")
    if "sheet_name" in kwargs:
        echo(f"Worksheet:  {kwargs['sheet_name']}")
    echo("Columns:")
    echo(", ".join(str(c) for c in sample.columns) if len(sample.columns) else "(none)")
    echo("")

    if not detected:
        echo("No sensitive columns were detected.")
        if not len(sample.columns):
            echo(
                "Tip: this spreadsheet may have a title above the table. "
                "Try --header-row with the row number that lists column names."
            )
        else:
            echo(
                "Tip: detection looks at column names and value patterns. "
                "If Email/Phone columns start further down the sheet, pass "
                "--header-row N (1-based)."
            )
        echo("Nothing to configure. Exiting without writing an output file.")
        raise Cancelled()

    term.bullet_ok(summarize_detection(detected))
    echo("")
    _print_detection_list(detected, echo)

    choices: dict[str, ColumnChoice] = {}
    while True:
        echo("")
        echo("Select a column to configure:")
        echo("")
        for index, item in enumerate(detected, start=1):
            marker = _selection_marker(item.column_name, choices)
            echo(f"[{index}] {marker} {item.column_name}")
            if item.column_name in choices and choices[item.column_name].configured:
                echo(f"      -> {choices[item.column_name].action_label}")
        echo("")
        echo("[d] Done")
        echo("[c] Clear selections")
        echo("[q] Cancel")
        echo("")

        answer = ask("> ").strip().lower()
        if answer in {"q", "quit", "cancel"}:
            raise Cancelled()
        if answer in {"c", "clear"}:
            choices.clear()
            term.bullet_ok("Cleared all column selections")
            continue
        if answer in {"d", "done"}:
            break
        if not answer.isdigit() or not (1 <= int(answer) <= len(detected)):
            echo("Enter a column number, d, c, or q.")
            continue

        selected = detected[int(answer) - 1]
        choice = _configure_column(selected, ask=ask, echo=echo)
        if choice is None:
            continue
        if choice.transform_type is None and choice.action_label == "Skip":
            choices.pop(selected.column_name, None)
            term.bullet_ok(f"{selected.column_name} skipped")
            continue
        choices[selected.column_name] = choice
        term.bullet_ok(f"{choice.column} -> {choice.action_label}")

    steps = choices_to_steps(choices)
    if not steps:
        echo("")
        echo("No transformations were configured.")
        raise Cancelled()

    if not _review(source, detected, choices, ask=ask, echo=echo, auto_confirm=auto_confirm):
        raise Cancelled()

    output_path = _choose_output(source, output, ask=ask, echo=echo)

    if _ask_yes_no("Save these transformations as a pipeline?", ask=ask, echo=echo):
        name = ask("Pipeline name: ").strip() or f"{source.stem} pipeline"
        pipeline_path = save_pipeline(steps, output_path, name=name)
        term.bullet_ok(f"Saved pipeline: {pipeline_path.name}")
        echo(f"  Re-run later with: deskx transform \"{source}\" --pipeline \"{name}\"")
        echo("")

    echo("DeskX")
    term.rule()
    echo("")
    echo("Input:")
    echo(str(source))
    echo("")
    echo("Output:")
    echo(str(output_path))
    echo("")

    seen: set[JobStatus] = set()

    def on_progress(update: ProgressUpdate) -> None:
        label = _STATUS_LABELS.get(update.status)
        if label and update.status not in seen:
            seen.add(update.status)
            term.bullet_ok(label)

    config = JobConfig(
        source_path=source,
        output_path=output_path,
        transform_steps=steps,
        header_row=kwargs.get("header_row", 0),
        sheet_name=kwargs.get("sheet_name", 0),
    )
    report = ProcessingJob(config, on_progress=on_progress).run()

    echo("")
    term.rule()
    echo("")
    echo("Completed successfully")
    echo("")
    if report.row_count is not None:
        echo(f"Rows processed: {report.row_count:,}")
    if report.column_count is not None:
        echo(f"Columns: {report.column_count:,}")
    echo("")
    echo("Output:")
    echo(str(output_path))
    echo("")
    return output_path


# ── Interactive steps ───────────────────────────────────────────────


def _configure_column(
    detected: SensitiveColumn,
    *,
    ask: AskFn,
    echo: EchoFn,
) -> ColumnChoice | None:
    echo("")
    echo("Column:")
    echo(detected.column_name)
    echo("")
    echo("Detected type:")
    echo(category_label(detected.category))
    echo("")
    echo("Choose transformation:")
    echo("")
    for key, label, _ in SANITIZE_ACTIONS:
        echo(f"[{key}] {label}")
    echo("")

    while True:
        raw = ask("> ").strip().lower()
        if raw in {"q", "quit"}:
            return None
        mapped = action_for_key(raw)
        if mapped is None:
            echo("Enter 1-6 (or q to go back).")
            continue
        label, transform_type = mapped
        break

    if transform_type is None:
        return ColumnChoice(
            column=detected.column_name,
            category=detected.category,
            action_label="Skip",
            transform_type=None,
        )

    params = _prompt_params(transform_type, detected.column_name, ask=ask, echo=echo)
    before, after = synthetic_example(transform_type, detected.category, params)

    echo("")
    echo(detected.column_name)
    echo("")
    echo("Transformation:")
    echo(label)
    echo("")
    echo("Configuration:")
    echo(_config_summary(transform_type, params))
    echo("")
    echo("Example:")
    echo(before)
    echo("->")
    echo(after)
    echo("")
    echo("Apply this transformation?")
    echo("[y] Yes")
    echo("[n] No")
    echo("")
    if not _ask_yes_no("", ask=ask, echo=echo, prompt="> "):
        return None

    return ColumnChoice(
        column=detected.column_name,
        category=detected.category,
        action_label=label,
        transform_type=transform_type,
        params=params,
        example_before=before,
        example_after=after,
    )


def _prompt_params(
    transform_type: TransformType,
    column: str,
    *,
    ask: AskFn,
    echo: EchoFn,
) -> dict:
    if transform_type is TransformType.MASK_COLUMN:
        echo("")
        echo("Choose masking style:")
        echo("")
        echo("[1] Show last 4 characters (default)")
        echo("[2] Fully mask")
        echo("[3] Custom visible length")
        echo("")
        while True:
            choice = ask("> ").strip()
            if choice in {"", "1"}:
                return default_params(transform_type, column, show_last=4)
            if choice == "2":
                return default_params(transform_type, column, show_last=0)
            if choice == "3":
                raw = ask("Characters to leave visible at the end: ").strip()
                try:
                    show_last = max(0, int(raw))
                except ValueError:
                    echo("Enter a whole number.")
                    continue
                return default_params(transform_type, column, show_last=show_last)
            echo("Enter 1, 2, or 3.")

    if transform_type is TransformType.REDACT_COLUMN:
        echo("")
        replacement = ask("Replacement text [[REDACTED]]: ").strip()
        if not replacement:
            replacement = "[REDACTED]"
        return default_params(transform_type, column, replacement=replacement)

    if transform_type is TransformType.PSEUDONYMIZE_COLUMN:
        echo("")
        prefix = ask("Pseudonym prefix [Person_]: ").strip() or "Person_"
        return default_params(transform_type, column, prefix=prefix)

    return default_params(transform_type, column)


def _config_summary(transform_type: TransformType, params: dict) -> str:
    if transform_type is TransformType.MASK_COLUMN:
        show_last = int(params.get("show_last", 4))
        if show_last == 0:
            return "Fully mask"
        return f"Show last {show_last} character(s)"
    if transform_type is TransformType.REDACT_COLUMN:
        return f"Replacement: {params.get('replacement', '[REDACTED]')}"
    if transform_type is TransformType.HASH_COLUMN:
        return "SHA-256"
    if transform_type is TransformType.PSEUDONYMIZE_COLUMN:
        return f"Prefix: {params.get('prefix', 'Person_')}"
    if transform_type is TransformType.REMOVE_COLUMNS:
        return "Drop column from output"
    return "(default settings)"


def _review(
    source: Path,
    detected: list[SensitiveColumn],
    choices: dict[str, ColumnChoice],
    *,
    ask: AskFn,
    echo: EchoFn,
    auto_confirm: bool,
) -> bool:
    echo("")
    echo("DeskX - Sanitization Review")
    term.rule()
    echo("")
    echo("Input:")
    echo(str(source))
    echo("")
    echo("Transformations:")
    echo("")
    configured = [c for c in choices.values() if c.configured]
    for choice in configured:
        echo(f"[OK] {choice.column}")
        echo(f"  -> {choice.action_label}")
        echo("")

    untouched = [
        item.column_name
        for item in detected
        if item.column_name not in choices or not choices[item.column_name].configured
    ]
    if untouched:
        echo("Columns detected but not configured:")
        echo("")
        for name in untouched:
            echo(f"* {name}")
        echo("")
        echo("These columns will NOT be modified.")
        echo("")

    if auto_confirm:
        return True

    echo("Continue?")
    echo("[y] Continue")
    echo("[n] Cancel")
    echo("")
    return _ask_yes_no("", ask=ask, echo=echo, prompt="> ")


def _choose_output(
    source: Path,
    output: str | None,
    *,
    ask: AskFn,
    echo: EchoFn,
) -> Path:
    if output is not None:
        return resolve_output_path(source, output)

    echo("Where should the sanitized file be saved?")
    echo("")
    echo("[y] Same folder as the source")
    echo("[o] Other folder")
    echo("[c] Cancel")
    echo("")
    while True:
        answer = ask("> ").strip().lower()
        if answer in {"c", "cancel", "q"}:
            raise Cancelled()
        if answer in {"y", "yes", "s", "same"}:
            candidate = source.parent / build_output_filename(source, SANITIZED_SUFFIX)
            break
        if answer in {"o", "other"}:
            raw = ask("Enter output directory: ").strip().strip('"').strip("'")
            if not raw:
                echo("Directory path is required.")
                continue
            directory = Path(raw).expanduser()
            directory.mkdir(parents=True, exist_ok=True)
            candidate = directory / build_output_filename(source, SANITIZED_SUFFIX)
            break
        echo("Enter y, o, or c.")

    if targets_same_file(source, candidate):
        raise DeskXError(
            f"That would overwrite the source file:\n  {source}\n"
            "Choose another folder or filename."
        )
    safe = next_available_path(candidate)
    ValidationService.validate_paths(source, safe)
    echo("")
    echo("Output will be:")
    echo(str(safe))
    echo("")
    return safe


def _print_detection_list(detected: list[SensitiveColumn], echo: EchoFn) -> None:
    echo("Detected sensitive columns:")
    echo("")
    for index, item in enumerate(detected, start=1):
        echo(f"[{index}] {item.column_name}")
        echo(f"    Type: {category_label(item.category)}")
        echo(f"    Confidence: {confidence_label(item.confidence)}")
        echo("")


def _selection_marker(column: str, choices: dict[str, ColumnChoice]) -> str:
    choice = choices.get(column)
    if choice and choice.configured:
        return "[OK]"
    return "[ ]"


def _ask_yes_no(
    question: str,
    *,
    ask: AskFn,
    echo: EchoFn,
    prompt: str = "> ",
) -> bool:
    if question:
        echo(question)
        echo("[y] Yes")
        echo("[n] No")
        echo("")
    while True:
        answer = ask(prompt).strip().lower()
        if answer in {"y", "yes"}:
            return True
        if answer in {"n", "no"}:
            return False
        echo("Enter y or n.")


def _default_ask(prompt: str) -> str:
    return typer.prompt(prompt, default="", show_default=False)
