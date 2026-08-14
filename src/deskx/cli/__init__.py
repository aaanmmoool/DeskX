"""DeskX command-line interface.

Thin Typer commands over the existing adapters, saved-pipeline helpers,
and :class:`~deskx.processing.job.ProcessingJob`.  No transformation or
I/O business logic lives here.
"""

from __future__ import annotations

from deskx.cli.main import app, main

__all__ = ["app", "main"]
