"""Per-job summary report generator.

Produces a JSON-serialisable report summarising what happened during a
processing run.  This is the foundation for a future audit trail.

This module has **no PySide6 dependency**.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class JobReport:
    """Immutable summary of a completed processing job."""

    source_path: str
    output_path: str
    source_hash: str
    output_hash: str
    status: str  # "success" | "error" | "cancelled"
    started_at: str
    finished_at: str
    duration_seconds: float
    row_count: int | None = None
    column_count: int | None = None
    columns_selected: list[str] = field(default_factory=list)
    error_message: str | None = None
    pipeline_summary: str | None = None

    # ── Serialisation ───────────────────────────────────────────────

    def to_dict(self) -> dict[str, Any]:
        """Return the report as a plain dictionary."""
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        """Return the report as a formatted JSON string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


class ReportGenerator:
    """Build :class:`JobReport` instances from processing context."""

    @staticmethod
    def build(
        *,
        source_path: Path,
        output_path: Path,
        source_hash: str,
        output_hash: str,
        status: str,
        started_at: datetime,
        finished_at: datetime | None = None,
        row_count: int | None = None,
        column_count: int | None = None,
        columns_selected: list[str] | None = None,
        error_message: str | None = None,
        pipeline_summary: str | None = None,
    ) -> JobReport:
        """Create a :class:`JobReport` from keyword arguments."""
        end = finished_at or datetime.now(timezone.utc)
        duration = (end - started_at).total_seconds()
        return JobReport(
            source_path=str(source_path),
            output_path=str(output_path),
            source_hash=source_hash,
            output_hash=output_hash,
            status=status,
            started_at=started_at.isoformat(),
            finished_at=end.isoformat(),
            duration_seconds=round(duration, 3),
            row_count=row_count,
            column_count=column_count,
            columns_selected=columns_selected or [],
            error_message=error_message,
            pipeline_summary=pipeline_summary,
        )
