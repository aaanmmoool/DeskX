"""Shared terminal formatting helpers for the DeskX CLI.

Windows consoles often use cp1252, so this module stays on plain ASCII
to avoid UnicodeEncodeError when printing rules or status marks.
"""

from __future__ import annotations

from typing import Iterable

import typer


def rule(char: str = "-", width: int = 36) -> None:
    typer.echo(char * width)


def section(title: str) -> None:
    typer.echo(title)


def kv(label: str, value: str) -> None:
    typer.echo(f"{label}:")
    typer.echo(value)
    typer.echo("")


def bullet_ok(message: str) -> None:
    typer.echo(f"[OK] {message}")


def bullet_fail(message: str) -> None:
    typer.echo(f"[X] {message}")


def echo_lines(lines: Iterable[str]) -> None:
    for line in lines:
        typer.echo(line)
