"""Transformation pipeline executor.

Accepts an ordered list of :class:`TransformStep` dataclasses, applies
each to the DataFrame in sequence, and produces a
:class:`PipelineResult` summarising what happened at each step.

This module has **no PySide6 dependency**.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable

import pandas as pd

from deskx.processing import transforms

logger = logging.getLogger(__name__)


# ── Transform catalogue ────────────────────────────────────────────


class TransformType(Enum):
    """Enumerates every available transform."""

    TRIM_WHITESPACE = auto()
    REMOVE_EMPTY_ROWS = auto()
    REMOVE_EMPTY_COLUMNS = auto()
    REMOVE_DUPLICATES = auto()
    REMOVE_COLUMNS = auto()
    RENAME_COLUMNS = auto()
    REORDER_COLUMNS = auto()
    FILL_MISSING = auto()
    NORMALIZE_DATES = auto()
    NORMALIZE_NUMBERS = auto()
    NORMALIZE_BOOLEANS = auto()
    FILTER_ROWS = auto()
    REPLACE_VALUES = auto()
    MASK_COLUMN = auto()
    REDACT_COLUMN = auto()
    HASH_COLUMN = auto()
    PSEUDONYMIZE_COLUMN = auto()
    GENERALIZE_COLUMN = auto()
    REVENUE_BANDS = auto()
    SUPPRESS_LOW_COUNTS = auto()


# Human-readable names and descriptions for the UI
TRANSFORM_INFO: dict[TransformType, dict[str, str]] = {
    TransformType.TRIM_WHITESPACE: {
        "name": "Trim Whitespace",
        "description": "Strip leading/trailing whitespace from all text columns",
        "category": "Cleaning",
    },
    TransformType.REMOVE_EMPTY_ROWS: {
        "name": "Remove Empty Rows",
        "description": "Drop rows where all values are empty or missing",
        "category": "Cleaning",
    },
    TransformType.REMOVE_EMPTY_COLUMNS: {
        "name": "Remove Empty Columns",
        "description": "Drop columns where all values are empty or missing",
        "category": "Cleaning",
    },
    TransformType.REMOVE_DUPLICATES: {
        "name": "Remove Duplicates",
        "description": "Remove duplicate rows",
        "category": "Cleaning",
    },
    TransformType.REMOVE_COLUMNS: {
        "name": "Remove Columns",
        "description": "Drop specified columns from the dataset",
        "category": "Columns",
    },
    TransformType.RENAME_COLUMNS: {
        "name": "Rename Columns",
        "description": "Rename columns using a mapping",
        "category": "Columns",
    },
    TransformType.REORDER_COLUMNS: {
        "name": "Reorder Columns",
        "description": "Change the order of columns",
        "category": "Columns",
    },
    TransformType.FILL_MISSING: {
        "name": "Fill Missing Values",
        "description": "Fill or drop missing values using a strategy",
        "category": "Missing Values",
    },
    TransformType.NORMALIZE_DATES: {
        "name": "Normalize Dates",
        "description": "Parse mixed date formats into a consistent format",
        "category": "Type Normalization",
    },
    TransformType.NORMALIZE_NUMBERS: {
        "name": "Normalize Numbers",
        "description": "Strip currency symbols and commas, convert to numeric",
        "category": "Type Normalization",
    },
    TransformType.NORMALIZE_BOOLEANS: {
        "name": "Normalize Booleans",
        "description": "Map yes/no/true/false/1/0 to boolean values",
        "category": "Type Normalization",
    },
    TransformType.FILTER_ROWS: {
        "name": "Filter Rows",
        "description": "Keep only rows matching a condition",
        "category": "Filtering",
    },
    TransformType.REPLACE_VALUES: {
        "name": "Replace Values",
        "description": "Find and replace values in a column",
        "category": "Filtering",
    },
    TransformType.MASK_COLUMN: {
        "name": "Mask",
        "description": "Mask values with asterisks (e.g. ****@com)",
        "category": "Privacy",
    },
    TransformType.REDACT_COLUMN: {
        "name": "Redact",
        "description": "Replace all values with [REDACTED]",
        "category": "Privacy",
    },
    TransformType.HASH_COLUMN: {
        "name": "Hash",
        "description": "Replace values with SHA-256 hashes",
        "category": "Privacy",
    },
    TransformType.PSEUDONYMIZE_COLUMN: {
        "name": "Pseudonymize",
        "description": "Replace with consistent fake identifiers",
        "category": "Privacy",
    },
    TransformType.GENERALIZE_COLUMN: {
        "name": "Generalize",
        "description": "Bin numeric values into ranges",
        "category": "Statistical Privacy",
    },
    TransformType.REVENUE_BANDS: {
        "name": "Revenue Bands",
        "description": "Categorize revenue into standard bands",
        "category": "Statistical Privacy",
    },
    TransformType.SUPPRESS_LOW_COUNTS: {
        "name": "Suppress Low Counts",
        "description": "Replace rare group values to prevent re-identification",
        "category": "Statistical Privacy",
    },
}


# ── Pipeline step ──────────────────────────────────────────────────


@dataclass
class TransformStep:
    """A single step in the transformation pipeline.

    Parameters
    ----------
    transform_type
        Which transform to apply.
    params
        Keyword arguments for the transform function.
    enabled
        Whether this step should be executed (allows disabling
        without removing).
    """

    transform_type: TransformType
    params: dict[str, Any] = field(default_factory=dict)
    enabled: bool = True


@dataclass
class StepResult:
    """Result of executing a single transform step."""

    step_name: str
    rows_before: int
    rows_after: int
    cols_before: int
    cols_after: int
    duration_ms: float
    success: bool
    error: str | None = None


@dataclass
class PipelineResult:
    """Summary of the entire pipeline execution."""

    steps: list[StepResult] = field(default_factory=list)
    total_rows_before: int = 0
    total_rows_after: int = 0
    total_cols_before: int = 0
    total_cols_after: int = 0
    total_duration_ms: float = 0.0
    success: bool = True

    def summary_text(self) -> str:
        """Return a human-readable summary."""
        lines = ["Pipeline Summary", "=" * 40]
        for i, step in enumerate(self.steps, 1):
            status = "✓" if step.success else "✗"
            delta_rows = step.rows_after - step.rows_before
            delta_cols = step.cols_after - step.cols_before
            parts = [f"  {status} Step {i}: {step.step_name}"]
            if delta_rows != 0:
                parts.append(f"    Rows: {delta_rows:+d}")
            if delta_cols != 0:
                parts.append(f"    Columns: {delta_cols:+d}")
            if step.error:
                parts.append(f"    Error: {step.error}")
            parts.append(f"    Duration: {step.duration_ms:.1f}ms")
            lines.extend(parts)

        lines.append("=" * 40)
        lines.append(
            f"Rows: {self.total_rows_before} → {self.total_rows_after}"
        )
        lines.append(
            f"Columns: {self.total_cols_before} → {self.total_cols_after}"
        )
        lines.append(f"Total time: {self.total_duration_ms:.1f}ms")
        return "\n".join(lines)


# ── Transform dispatcher ──────────────────────────────────────────

# Maps TransformType → the function to call.
# The function signature is always (df, **params) → df.
_DISPATCH: dict[TransformType, Callable[..., pd.DataFrame]] = {
    TransformType.TRIM_WHITESPACE: lambda df, **kw: transforms.trim_whitespace(df),
    TransformType.REMOVE_EMPTY_ROWS: lambda df, **kw: transforms.remove_empty_rows(df),
    TransformType.REMOVE_EMPTY_COLUMNS: lambda df, **kw: transforms.remove_empty_columns(df),
    TransformType.REMOVE_DUPLICATES: lambda df, **kw: transforms.remove_duplicates(df, **kw),
    TransformType.REMOVE_COLUMNS: lambda df, **kw: transforms.remove_columns(df, **kw),
    TransformType.RENAME_COLUMNS: lambda df, **kw: transforms.rename_columns(df, **kw),
    TransformType.REORDER_COLUMNS: lambda df, **kw: transforms.reorder_columns(df, **kw),
    TransformType.FILL_MISSING: lambda df, **kw: transforms.fill_missing(df, **kw),
    TransformType.NORMALIZE_DATES: lambda df, **kw: transforms.normalize_dates(df, **kw),
    TransformType.NORMALIZE_NUMBERS: lambda df, **kw: transforms.normalize_numbers(df, **kw),
    TransformType.NORMALIZE_BOOLEANS: lambda df, **kw: transforms.normalize_booleans(df, **kw),
    TransformType.FILTER_ROWS: lambda df, **kw: transforms.filter_rows(df, **kw),
    TransformType.REPLACE_VALUES: lambda df, **kw: transforms.replace_values(df, **kw),
    TransformType.MASK_COLUMN: lambda df, **kw: transforms.mask_column(df, **kw),
    TransformType.REDACT_COLUMN: lambda df, **kw: transforms.redact_column(df, **kw),
    TransformType.HASH_COLUMN: lambda df, **kw: transforms.hash_column(df, **kw),
    TransformType.PSEUDONYMIZE_COLUMN: lambda df, **kw: transforms.pseudonymize_column(df, **kw),
    TransformType.GENERALIZE_COLUMN: lambda df, **kw: transforms.generalize_column(df, **kw),
    TransformType.REVENUE_BANDS: lambda df, **kw: transforms.revenue_bands(df, **kw),
    TransformType.SUPPRESS_LOW_COUNTS: lambda df, **kw: transforms.suppress_low_counts(df, **kw),
}


# ── Pipeline executor ─────────────────────────────────────────────


def execute_pipeline(
    df: pd.DataFrame,
    steps: list[TransformStep],
) -> tuple[pd.DataFrame, PipelineResult]:
    """Execute an ordered list of transforms on *df*.

    Returns the transformed DataFrame and a :class:`PipelineResult`.
    Steps that fail are logged and skipped — the pipeline continues.
    """
    result = PipelineResult(
        total_rows_before=len(df),
        total_cols_before=len(df.columns),
    )

    current = df.copy()
    total_start = time.perf_counter()

    for step in steps:
        if not step.enabled:
            continue

        info = TRANSFORM_INFO.get(step.transform_type, {})
        step_name = info.get("name", step.transform_type.name)
        rows_before = len(current)
        cols_before = len(current.columns)

        t0 = time.perf_counter()
        try:
            func = _DISPATCH.get(step.transform_type)
            if func is None:
                raise ValueError(
                    f"Unknown transform: {step.transform_type}"
                )
            current = func(current, **step.params)
            step_result = StepResult(
                step_name=step_name,
                rows_before=rows_before,
                rows_after=len(current),
                cols_before=cols_before,
                cols_after=len(current.columns),
                duration_ms=(time.perf_counter() - t0) * 1000,
                success=True,
            )
        except Exception as exc:
            logger.exception("Transform step '%s' failed", step_name)
            step_result = StepResult(
                step_name=step_name,
                rows_before=rows_before,
                rows_after=rows_before,
                cols_before=cols_before,
                cols_after=cols_before,
                duration_ms=(time.perf_counter() - t0) * 1000,
                success=False,
                error=str(exc),
            )
            result.success = False

        result.steps.append(step_result)

    total_end = time.perf_counter()
    result.total_rows_after = len(current)
    result.total_cols_after = len(current.columns)
    result.total_duration_ms = (total_end - total_start) * 1000

    return current, result
