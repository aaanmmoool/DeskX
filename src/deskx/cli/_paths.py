"""Path helpers shared by CLI commands."""

from __future__ import annotations

from pathlib import Path

import typer

from deskx.core.exceptions import SamePathError, ValidationError
from deskx.core.config import SANITIZED_SUFFIX, get_managed_output_dir
from deskx.core.utils import (
    build_output_filename,
    next_available_path,
    targets_same_file,
)
from deskx.processing.validation_service import ValidationService


def resolve_existing_file(raw: str | Path, *, label: str = "File") -> Path:
    """Resolve a user-supplied path to an existing file.

    Strips accidental quotes from shell pasting and prints a clear error
    when the path is missing — Windows users often hit Click's generic
    "does not exist" when quotes or cwd differ from expectation.
    """
    text = str(raw).strip().strip('"').strip("'")
    if not text:
        typer.secho(f"{label} path is empty.", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=2)

    path = Path(text).expanduser()
    if not path.exists():
        typer.secho(
            f"{label} not found:\n  {path}\n"
            "Check the path, keep quotes around paths with spaces, and "
            "confirm the file is still there.",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=2)
    if not path.is_file():
        typer.secho(
            f"{label} must be a file, not a folder:\n  {path}",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=2)
    return path.resolve()


def resolve_output_path(source: Path, output: Path | str | None) -> Path:
    """Pick a safe output path that never overwrites the source.

    * ``None`` → ``Documents/DeskX/Output/<stem>_sanitized<ext>``
    * directory → same naming inside that folder
    * file path → that file (or a numbered version if it already exists)

    Existing outputs are never silently replaced.
    """
    source = Path(source)

    if output is None:
        directory = get_managed_output_dir(create=True)
        candidate = directory / build_output_filename(source, SANITIZED_SUFFIX)
    else:
        target = Path(str(output).strip().strip('"').strip("'")).expanduser()
        if target.exists() and target.is_dir():
            candidate = target / build_output_filename(source, SANITIZED_SUFFIX)
        elif target.suffix.lower() == "" and not target.exists():
            # Treat extension-less paths as directories the user wants created.
            target.mkdir(parents=True, exist_ok=True)
            candidate = target / build_output_filename(source, SANITIZED_SUFFIX)
        else:
            candidate = target
            if candidate.parent and not candidate.parent.exists():
                raise ValidationError(
                    f"Output directory does not exist: '{candidate.parent}'"
                )

    if targets_same_file(source, candidate):
        raise SamePathError(str(source))

    safe = next_available_path(candidate)
    ValidationService.validate_paths(source, safe)
    return safe
