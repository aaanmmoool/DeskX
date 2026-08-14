"""``deskx preview`` — inspect a dataset without loading it all."""

from __future__ import annotations

from typing import Annotated, Optional

import typer

from deskx.adapters.adapter_registry import create_default_registry
from deskx.cli import _terminal as term
from deskx.cli._import_options import resolve_import_kwargs
from deskx.cli._paths import resolve_existing_file
from deskx.core.exceptions import DeskXError, UnsupportedFormatError


def preview_command(
    file: Annotated[
        str,
        typer.Argument(help="Dataset to preview (CSV, XLSX, JSON, or TXT)."),
    ],
    rows: Annotated[
        int,
        typer.Option("--rows", min=1, help="Number of preview rows to show."),
    ] = 5,
    sheet: Annotated[
        Optional[str],
        typer.Option("--sheet", help="Worksheet name (XLSX only)."),
    ] = None,
    header_row: Annotated[
        Optional[int],
        typer.Option(
            "--header-row",
            help="1-based row number that contains column names.",
            min=1,
        ),
    ] = None,
) -> None:
    """Preview a dataset.

    Shows metadata and the first few rows without loading the whole file
    when the adapter supports bounded reads.
    """
    path = resolve_existing_file(file, label="Dataset")
    registry = create_default_registry()

    try:
        adapter = registry.get(path.suffix)
    except UnsupportedFormatError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=2) from exc

    try:
        kwargs = resolve_import_kwargs(
            path,
            registry=registry,
            sheet=sheet,
            header_row=None if header_row is None else header_row - 1,
        )
    except ValueError as exc:
        typer.secho(str(exc), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=2) from exc
    except Exception as exc:  # noqa: BLE001
        typer.secho(f"Could not open workbook: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc

    try:
        frame = adapter.read_preview(path, max_rows=rows, **kwargs)
        frame = frame.dropna(axis=1, how="all")
    except Exception as exc:  # noqa: BLE001
        if isinstance(exc, DeskXError):
            typer.secho(str(exc), fg=typer.colors.RED, err=True)
        else:
            typer.secho(f"Failed to preview file: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc

    term.section("DeskX Preview")
    term.rule()
    typer.echo(f"File:       {path.name}")
    typer.echo(f"Path:       {path}")
    typer.echo(f"Format:     {adapter.display_name}")
    if "sheet_name" in kwargs:
        typer.echo(f"Worksheet:  {kwargs['sheet_name']}")
    typer.echo(f"Header row: {int(kwargs.get('header_row', 0)) + 1}")
    typer.echo(f"Columns:    {len(frame.columns)}")
    typer.echo(f"Preview:    first {len(frame)} row(s)")
    typer.echo("")
    typer.echo("Column names:")
    typer.echo(", ".join(str(c) for c in frame.columns) if len(frame.columns) else "(none)")
    typer.echo("")

    if path.suffix.lower() == ".json":
        _print_json_preview(frame)
    else:
        if frame.empty:
            typer.echo("(no rows)")
        else:
            typer.echo(frame.to_string(index=True))
    term.rule()


def _print_json_preview(frame) -> None:
    """Show the first JSON object in a readable key/value form."""
    if frame.empty:
        typer.echo("(empty JSON)")
        return

    record = frame.iloc[0].to_dict()
    typer.echo("First object:")
    for key, value in record.items():
        typer.echo(f"  {key}: {value}")
    if len(frame) > 1:
        typer.echo("")
        typer.echo(f"({len(frame) - 1} additional object(s) not shown)")
