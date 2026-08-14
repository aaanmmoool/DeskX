"""DeskX CLI entry point.

Architecture::

    deskx sanitize / preview / transform / pipeline
              │
              ▼
    Existing adapters, detector, saved-pipeline helpers, ProcessingJob
              │
              ▼
    Existing pipeline engine + transforms + reports

The CLI contains no transformation or file-format business logic.
"""

from __future__ import annotations

from typing import Annotated, Optional

import typer

from deskx.cli.pipeline import app as pipeline_app
from deskx.cli.preview import preview_command
from deskx.cli.sanitize import sanitize_command
from deskx.cli.transform import transform_command
from deskx.core.config import APP_VERSION

app = typer.Typer(
    name="deskx",
    help=(
        "DeskX - Data Sanitization CLI\n\n"
        "Usage:\n"
        "    deskx <command> [options]\n\n"
        "Commands:\n\n"
        "    sanitize      Interactively sanitize sensitive columns\n"
        "    preview       Preview a dataset\n"
        "    transform     Transform a dataset using a saved pipeline\n"
        "    pipeline      Manage saved pipelines\n"
        "    version       Show DeskX version\n"
        "    gui           Launch the DeskX desktop application\n\n"
        "Pipeline commands:\n\n"
        "    pipeline list\n"
        "    pipeline show\n"
        "    pipeline validate\n\n"
        "Run:\n\n"
        "    deskx <command> --help"
    ),
    no_args_is_help=True,
    add_completion=False,
    rich_markup_mode=None,
    context_settings={"help_option_names": ["-h", "--help"]},
)

app.command("sanitize")(sanitize_command)
app.command("preview")(preview_command)
app.command("transform")(transform_command)
app.add_typer(pipeline_app, name="pipeline")


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"DeskX {APP_VERSION}")
        raise typer.Exit()


@app.callback()
def root(
    version: Annotated[
        Optional[bool],
        typer.Option(
            "--version",
            callback=_version_callback,
            is_eager=True,
            help="Show DeskX version and exit.",
        ),
    ] = None,
) -> None:
    """DeskX - Data Sanitization CLI."""
    _ = version


@app.command("version")
def version_command() -> None:
    """Show DeskX version."""
    typer.echo(f"DeskX {APP_VERSION}")
    typer.echo("DeskX - Data Transformation Tool")


@app.command("gui")
def gui_command() -> None:
    """Launch the DeskX desktop application."""
    from deskx.main import main as gui_main

    raise typer.Exit(code=gui_main())


def main() -> None:
    """Console-script entry point."""
    app()


if __name__ == "__main__":
    main()
