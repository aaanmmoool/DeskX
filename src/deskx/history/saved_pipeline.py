"""Portable JSON persistence for user-configured transformation pipelines.

The GUI already uses :func:`save_pipeline` to write a JSON recipe beside
a successful output.  This module also provides the load / discover /
validate helpers the CLI (and future API) need — without changing how
pipelines are saved from the desktop app.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from deskx.core.config import (
    APP_NAME,
    APP_VERSION,
    get_app_data_dir,
    get_documents_dir,
    get_managed_output_dir,
)
from deskx.core.exceptions import DeskXError, ValidationError
from deskx.core.utils import next_available_path
from deskx.processing.pipeline import TransformStep, TransformType
from deskx.processing.transform_catalog import TRANSFORM_CATALOG

PIPELINE_SCHEMA_VERSION = 1
_PIPELINE_SUFFIX = "_pipeline"
_VERSIONED_NAME = re.compile(r"^(?P<base>.+?)(?: \((?P<n>\d+)\))?$")


class PipelineLoadError(DeskXError):
    """Raised when a saved pipeline cannot be read or interpreted."""


@dataclass(frozen=True)
class PipelineValidationIssue:
    """One concrete reason a pipeline document is invalid."""

    message: str


@dataclass(frozen=True)
class PipelineValidationResult:
    """Outcome of :func:`validate_pipeline` / :func:`validate_pipeline_document`."""

    ok: bool
    issues: tuple[PipelineValidationIssue, ...] = ()

    @property
    def error_messages(self) -> list[str]:
        return [issue.message for issue in self.issues]


@dataclass(frozen=True)
class SavedPipeline:
    """A discovered or loaded pipeline recipe."""

    path: Path
    name: str
    description: str
    steps: tuple[TransformStep, ...]
    document: dict[str, Any] = field(repr=False)

    @property
    def step_count(self) -> int:
        return len(self.steps)


def pipeline_path_for_output(output_path: Path) -> Path:
    """Return a non-conflicting pipeline path beside *output_path*."""
    proposed = output_path.with_name(f"{output_path.stem}_pipeline.json")
    return next_available_path(proposed)


def pipeline_payload(
    steps: Iterable[TransformStep],
    *,
    name: str | None = None,
    description: str | None = None,
) -> dict[str, Any]:
    """Convert transformation steps to a stable, portable JSON document."""
    payload: dict[str, Any] = {
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
    if name:
        payload["name"] = name
    if description:
        payload["description"] = description
    return payload


def save_pipeline(
    steps: Iterable[TransformStep],
    output_path: Path,
    *,
    name: str | None = None,
    description: str | None = None,
) -> Path:
    """Atomically save *steps* beside an output file and return its path.

    Existing pipeline files are never overwritten. A numbered version is
    selected using the same safe naming behavior as processed outputs.
    """
    target = pipeline_path_for_output(output_path)
    temporary = target.with_name(f".{target.name}.tmp")
    payload = pipeline_payload(steps, name=name, description=description)

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


def get_pipeline_search_dirs() -> list[Path]:
    """Directories DeskX scans when resolving a pipeline by name."""
    dirs: list[Path] = []
    deskx_docs = get_documents_dir() / APP_NAME
    for candidate in (
        get_managed_output_dir(create=False),
        deskx_docs,
        get_app_data_dir() / "pipelines",
        Path.cwd(),
        Path.home() / "Downloads",
    ):
        if candidate not in dirs:
            dirs.append(candidate)
    return dirs


def display_name_for(path: Path, document: dict[str, Any] | None = None) -> str:
    """Human-readable pipeline name from the JSON document or file name."""
    if document:
        named = document.get("name")
        if isinstance(named, str) and named.strip():
            return named.strip()

    stem = path.stem
    if stem.endswith(_PIPELINE_SUFFIX):
        stem = stem[: -len(_PIPELINE_SUFFIX)]
    match = _VERSIONED_NAME.match(stem)
    if match:
        stem = match.group("base")
    return stem.replace("_", " ").strip() or path.stem


def load_pipeline_document(path: Path) -> dict[str, Any]:
    """Read and parse a pipeline JSON file."""
    target = Path(path)
    if not target.is_file():
        raise PipelineLoadError(f"Pipeline file not found: '{target}'")
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PipelineLoadError(
            f"Pipeline file is not valid JSON: '{target}' ({exc.msg})"
        ) from exc
    if not isinstance(data, dict):
        raise PipelineLoadError(
            f"Pipeline file must contain a JSON object: '{target}'"
        )
    return data


def steps_from_document(document: dict[str, Any]) -> list[TransformStep]:
    """Build :class:`TransformStep` objects from a pipeline document."""
    result = validate_pipeline_document(document)
    if not result.ok:
        raise PipelineLoadError("; ".join(result.error_messages))

    steps: list[TransformStep] = []
    for entry in document.get("steps", []):
        transform_type = TransformType[entry["transform_type"]]
        params = entry.get("params") or {}
        enabled = entry.get("enabled", True)
        steps.append(
            TransformStep(
                transform_type=transform_type,
                params=dict(params),
                enabled=bool(enabled),
            )
        )
    return steps


def load_pipeline(path: Path) -> SavedPipeline:
    """Load a saved pipeline file into a :class:`SavedPipeline`."""
    target = Path(path)
    document = load_pipeline_document(target)
    steps = steps_from_document(document)
    description = document.get("description")
    if not isinstance(description, str):
        description = ""
    return SavedPipeline(
        path=target.resolve(),
        name=display_name_for(target, document),
        description=description.strip(),
        steps=tuple(steps),
        document=document,
    )


def validate_pipeline_document(document: dict[str, Any]) -> PipelineValidationResult:
    """Validate a pipeline JSON object without touching a dataset."""
    issues: list[PipelineValidationIssue] = []

    if not isinstance(document, dict):
        return PipelineValidationResult(
            False,
            (PipelineValidationIssue("Pipeline document must be a JSON object."),),
        )

    schema = document.get("schema_version", PIPELINE_SCHEMA_VERSION)
    if schema is not None and not isinstance(schema, int):
        issues.append(
            PipelineValidationIssue("schema_version must be an integer when present.")
        )
    elif isinstance(schema, int) and schema > PIPELINE_SCHEMA_VERSION:
        issues.append(
            PipelineValidationIssue(
                f"Unsupported schema_version {schema} "
                f"(this DeskX build understands up to {PIPELINE_SCHEMA_VERSION})."
            )
        )

    steps = document.get("steps")
    if steps is None:
        issues.append(
            PipelineValidationIssue("Pipeline is missing the required 'steps' list.")
        )
        return PipelineValidationResult(False, tuple(issues))
    if not isinstance(steps, list):
        issues.append(PipelineValidationIssue("'steps' must be a list."))
        return PipelineValidationResult(False, tuple(issues))
    if not steps:
        issues.append(
            PipelineValidationIssue("Pipeline contains no transformation steps.")
        )

    known = {member.name for member in TransformType}
    for index, entry in enumerate(steps, start=1):
        prefix = f"Step {index}"
        if not isinstance(entry, dict):
            issues.append(PipelineValidationIssue(f"{prefix} must be a JSON object."))
            continue

        transform_name = entry.get("transform_type")
        if not isinstance(transform_name, str) or not transform_name.strip():
            issues.append(
                PipelineValidationIssue(f"{prefix} is missing a transform_type.")
            )
        elif transform_name not in known:
            issues.append(
                PipelineValidationIssue(
                    f"{prefix} uses unknown transform_type '{transform_name}'."
                )
            )

        params = entry.get("params", {})
        if params is None:
            params = {}
        if not isinstance(params, dict):
            issues.append(
                PipelineValidationIssue(f"{prefix} params must be a JSON object.")
            )
        else:
            issues.extend(_validate_step_params(prefix, transform_name, params))

        if "enabled" in entry and not isinstance(entry["enabled"], bool):
            issues.append(
                PipelineValidationIssue(
                    f"{prefix} enabled flag must be true or false."
                )
            )

    return PipelineValidationResult(not issues, tuple(issues))


def validate_pipeline(path: Path) -> PipelineValidationResult:
    """Validate a saved pipeline file on disk."""
    try:
        document = load_pipeline_document(path)
    except PipelineLoadError as exc:
        return PipelineValidationResult(
            False, (PipelineValidationIssue(str(exc)),)
        )
    return validate_pipeline_document(document)


def _iter_pipeline_files(directory: Path) -> list[Path]:
    """Return pipeline JSON files under *directory* (non-recursive + one level)."""
    if not directory.is_dir():
        return []
    found: list[Path] = []
    found.extend(directory.glob("*_pipeline*.json"))
    # One extra level catches Documents/DeskX/Output without a deep walk.
    found.extend(directory.glob("*/*_pipeline*.json"))
    return [path for path in found if path.is_file()]


def list_pipelines(search_dirs: Iterable[Path] | None = None) -> list[SavedPipeline]:
    """Discover saved pipelines under the usual DeskX folders."""
    directories = list(search_dirs) if search_dirs is not None else get_pipeline_search_dirs()
    found: dict[Path, SavedPipeline] = {}

    for directory in directories:
        for path in sorted(_iter_pipeline_files(directory)):
            resolved = path.resolve()
            if resolved in found:
                continue
            try:
                found[resolved] = load_pipeline(path)
            except (PipelineLoadError, OSError, ValidationError):
                continue

    return sorted(found.values(), key=lambda item: item.name.lower())


def resolve_pipeline(
    name_or_path: str,
    search_dirs: Iterable[Path] | None = None,
) -> SavedPipeline:
    """Resolve a pipeline by filesystem path or discoverable display name."""
    raw = str(name_or_path).strip().strip('"').strip("'")
    if not raw:
        raise PipelineLoadError("Pipeline name or path is required.")

    candidate = Path(raw).expanduser()
    if candidate.is_file():
        return load_pipeline(candidate)

    needle = raw.casefold()
    matches = [
        pipeline
        for pipeline in list_pipelines(search_dirs)
        if pipeline.name.casefold() == needle
        or pipeline.path.stem.casefold() == needle
        or pipeline.path.name.casefold() == needle
    ]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        locations = ", ".join(str(item.path) for item in matches)
        raise PipelineLoadError(
            f"Multiple pipelines named '{raw}' were found: {locations}"
        )
    raise PipelineLoadError(
        f"No saved pipeline named '{raw}' was found. "
        "Use a full path to the *_pipeline.json file, or run "
        "'deskx pipeline list'."
    )


def format_step_summary(step: TransformStep) -> tuple[str, list[str]]:
    """Return a friendly title and detail lines for terminal display."""
    meta = TRANSFORM_CATALOG.get(step.transform_type)
    title = (
        meta.friendly_name
        if meta
        else step.transform_type.name.replace("_", " ").title()
    )
    details: list[str] = []

    params = step.params or {}
    columns = params.get("column") or params.get("columns") or params.get("subset")
    if columns:
        if isinstance(columns, list):
            details.append(f"Columns: {', '.join(str(c) for c in columns)}")
        else:
            details.append(f"Columns: {columns}")

    for key, value in params.items():
        if key in {"column", "columns", "subset"} or value in ("", None):
            continue
        label = key.replace("_", " ").title()
        details.append(f"{label}: {value}")

    if not step.enabled:
        details.append("Enabled: false")

    return title, details


def _validate_step_params(
    prefix: str,
    transform_name: Any,
    params: dict[str, Any],
) -> list[PipelineValidationIssue]:
    """Light structural checks — never invent transform-specific engines."""
    issues: list[PipelineValidationIssue] = []

    for key in ("column", "columns", "subset"):
        if key not in params:
            continue
        value = params[key]
        if key == "column" and not isinstance(value, str):
            issues.append(
                PipelineValidationIssue(f"{prefix} '{key}' must be a string.")
            )
        if key in {"columns", "subset"} and not isinstance(value, list):
            issues.append(
                PipelineValidationIssue(
                    f"{prefix} '{key}' must be a list of strings."
                )
            )

    if (
        isinstance(transform_name, str)
        and transform_name
        in {
            "MASK_COLUMN",
            "REDACT_COLUMN",
            "HASH_COLUMN",
            "PSEUDONYMIZE_COLUMN",
            "GENERALIZE_COLUMN",
            "REVENUE_BANDS",
        }
        and not params.get("column")
        and not params.get("columns")
    ):
        issues.append(
            PipelineValidationIssue(
                f"{prefix} ({transform_name}) requires a 'column' (or 'columns') setting."
            )
        )

    return issues
