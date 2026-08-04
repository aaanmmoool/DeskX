"""Progress event dataclasses.

These are the **only** objects that cross the processing → GUI boundary.
They are plain Python dataclasses — no PySide6 types — so the processing
engine remains fully decoupled from the GUI framework.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProgressEvent:
    """Emitted periodically during processing."""

    message: str
    percent: int  # 0–100


@dataclass(frozen=True)
class CompletionEvent:
    """Emitted when processing finishes successfully."""

    message: str
    report_json: str  # Serialised JobReport


@dataclass(frozen=True)
class ErrorEvent:
    """Emitted when processing fails."""

    message: str
    is_cancellation: bool = False
