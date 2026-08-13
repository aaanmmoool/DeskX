"""Portable JSON persistence for user-configured transformation pipelines."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from deskx.core.config import APP_NAME, APP_VERSION
from deskx.core.utils import next_available_path
from deskx.processing.pipeline import TransformStep

PIPELINE_SCHEMA_VERSION = 1


def pipeline_path_for_output(output_path: Path) -> Path:
    """Return a non-conflicting pipeline path beside *output_path*."""
    proposed = output_path.with_name(f"{output_path.stem}_pipeline.json")
    return next_available_path(proposed)


def pipeline_payload(steps: Iterable[TransformStep]) -> dict[str, Any]:
    """Convert transformation steps to a stable, portable JSON document."""
    return {
        "schema_version": PIPELINE_SCHEMA_VERSION,
        "application": APP_NAME,
        "application_version": APP_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "steps": [
            {
                "transform_type": step.transform_type.name,
                "enabled": step.enabled,
                "params": step.params,
            }
            for step in steps
        ],
    }


def save_pipeline(steps: Iterable[TransformStep], output_path: Path) -> Path:
    """Atomically save *steps* beside an output file and return its path.

    Existing pipeline files are never overwritten. A numbered version is
    selected using the same safe naming behavior as processed outputs.
    """
    target = pipeline_path_for_output(output_path)
    temporary = target.with_name(f".{target.name}.tmp")
    payload = pipeline_payload(steps)

    try:
        temporary.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, target)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise

    return target
