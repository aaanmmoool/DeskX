"""``deskx transform`` — run a saved pipeline through ProcessingJob."""

from __future__ import annotations

from typing import Annotated, Optional

import typer

from deskx.cli import _terminal as term
from deskx.cli._paths import resolve_existing_file, resolve_output_path
from deskx.core.exceptions import DeskXError
from deskx.history.saved_pipeline import (
    PipelineLoadError,
    format_step_summary,
    resolve_pipeline,
)
from deskx.processing.job import JobConfig, JobStatus, ProcessingJob, ProgressUpdate

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


def transform_command(
    file: Annotated[
        str,
        typer.Argument(help="Source dataset to transform."),
    ],
    pipeline: Annotated[
        str,
        typer.Option(
            "--pipeline",
            "-p",
            help="Saved pipeline name or path to a *_pipeline.json file.",
        ),
    ],
    output: Annotated[
        Optional[str],
        typer.Option(
            "--output",
            "-o",
            help="Output file or directory. Defaults to Documents/DeskX/Output.",
        ),
    ] = None,
    sheet: Annotated[
        Optional[str],
        typer.Option("--sheet", help="Worksheet name (XLSX only)."),
    ] = None,
) -> None:
    """Transform a dataset using a saved pipeline.

    Runs the existing ProcessingJob end to end — the CLI does not
    execute transforms itself.
    """
    source = resolve_existing_file(file, label="Dataset")

    try:
        saved = resolve_pipeline(pipeline)
    except PipelineLoadError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=2) from exc

    try:
        output_path = resolve_output_path(source, output)
    except DeskXError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=2) from exc

    typer.echo("DeskX")
    term.rule()
    typer.echo("")
    typer.echo("Input:")
    typer.echo(str(source))
    typer.echo("")
    typer.echo("Pipeline:")
    typer.echo(saved.name)
    typer.echo("")

    term.bullet_ok("Loaded pipeline")
    for index, step in enumerate(saved.steps, start=1):
        title, _ = format_step_summary(step)
        if step.enabled:
            typer.echo(f"  {index}. {title}")

    seen: set[JobStatus] = set()

    def on_progress(update: ProgressUpdate) -> None:
        label = _STATUS_LABELS.get(update.status)
        if label and update.status not in seen:
            seen.add(update.status)
            term.bullet_ok(label)

    config = JobConfig(
        source_path=source,
        output_path=output_path,
        transform_steps=list(saved.steps),
        sheet_name=sheet if sheet is not None else 0,
    )

    try:
        report = ProcessingJob(config, on_progress=on_progress).run()
    except DeskXError as exc:
        typer.echo("")
        term.bullet_fail(str(exc))
        raise typer.Exit(code=1) from exc
    except Exception as exc:  # noqa: BLE001
        typer.echo("")
        term.bullet_fail(f"Processing failed: {exc}")
        raise typer.Exit(code=1) from exc

    typer.echo("")
    term.rule()
    typer.echo("")
    typer.echo("Completed successfully")
    typer.echo("")
    if report.row_count is not None:
        typer.echo(f"Rows processed: {report.row_count:,}")
    if report.column_count is not None:
        typer.echo(f"Columns: {report.column_count:,}")
    typer.echo("")
    typer.echo("Output:")
    typer.echo(str(output_path))
    if report.source_hash:
        typer.echo("")
        typer.echo(f"Source hash: {report.source_hash}")
        typer.echo(f"Output hash: {report.output_hash}")
    typer.echo("")
