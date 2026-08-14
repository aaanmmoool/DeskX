"""``deskx pipeline`` — inspect and validate saved pipelines."""

from __future__ import annotations

from typing import Annotated

import typer

from deskx.cli import _terminal as term
from deskx.history.saved_pipeline import (
    PipelineLoadError,
    format_step_summary,
    list_pipelines,
    resolve_pipeline,
    validate_pipeline,
)

app = typer.Typer(
    help="Manage saved transformation pipelines.",
    no_args_is_help=True,
)


@app.command("list")
def pipeline_list() -> None:
    """List all discoverable saved pipelines."""
    pipelines = list_pipelines()
    if not pipelines:
        typer.echo("No saved pipelines found.")
        typer.echo("")
        typer.echo("Pipelines are written beside sanitized outputs when you tick")
        typer.echo("'Save pipeline configuration' in the desktop app, or place")
        typer.echo("*_pipeline.json files in Documents/DeskX/Output.")
        return

    typer.echo("Available pipelines:")
    typer.echo("")
    for pipeline in pipelines:
        typer.echo(f"  {pipeline.name}")
        typer.echo(f"    {pipeline.path}")
        typer.echo(f"    {pipeline.step_count} step(s)")
        typer.echo("")


@app.command("show")
def pipeline_show(
    pipeline: Annotated[
        str,
        typer.Argument(help="Pipeline display name or path to a *_pipeline.json file."),
    ],
) -> None:
    """Show a saved pipeline's ordered steps and configuration."""
    try:
        saved = resolve_pipeline(pipeline)
    except PipelineLoadError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=2) from exc

    typer.echo(f"Pipeline: {saved.name}")
    if saved.description:
        typer.echo("")
        typer.echo(saved.description)
    typer.echo("")
    typer.echo(f"File: {saved.path}")
    typer.echo("")

    if not saved.steps:
        typer.echo("(no steps)")
        return

    for index, step in enumerate(saved.steps, start=1):
        title, details = format_step_summary(step)
        typer.echo(f"{index}. {title}")
        for detail in details:
            typer.echo(f"   {detail}")
    typer.echo("")


@app.command("validate")
def pipeline_validate(
    pipeline: Annotated[
        str,
        typer.Argument(help="Pipeline display name or path to a *_pipeline.json file."),
    ],
) -> None:
    """Validate a saved pipeline without processing a dataset."""
    from pathlib import Path

    from deskx.history.saved_pipeline import (
        display_name_for,
        load_pipeline_document,
    )

    candidate = Path(pipeline).expanduser()
    if candidate.is_file():
        target = candidate
        try:
            document = load_pipeline_document(target)
            name = display_name_for(target, document)
        except Exception:  # noqa: BLE001 — still validate via the file API below
            name = candidate.name
            document = None
    else:
        try:
            saved = resolve_pipeline(pipeline)
        except PipelineLoadError as exc:
            term.bullet_fail("Pipeline is invalid")
            typer.echo(str(exc))
            raise typer.Exit(code=2) from exc
        target = saved.path
        name = saved.name
        document = None

    result = validate_pipeline(target)
    if result.ok:
        term.bullet_ok("Pipeline is valid")
        typer.echo(f"Pipeline: {name}")
        if document is not None:
            steps = document.get("steps") or []
            typer.echo(f"Steps: {len(steps)}")
        raise typer.Exit(code=0)

    term.bullet_fail("Pipeline is invalid")
    for message in result.error_messages:
        typer.echo(f"  - {message}")
    raise typer.Exit(code=1)
