"""Data transformation functions.

Every function here is a pure function: ``DataFrame → DataFrame``.
They do **not** mutate the input — each returns a new DataFrame.

This module has **no PySide6 dependency**.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any, Literal

import pandas as pd
import numpy as np


# ── Cleaning ────────────────────────────────────────────────────────


def trim_whitespace(df: pd.DataFrame) -> pd.DataFrame:
    """Strip leading/trailing whitespace from all string columns.

    Also collapses interior runs of whitespace to a single space
    and strips whitespace from column names.
    """
    result = df.copy()

    # Save NaN masks before renaming (keyed by positional index)
    nan_masks: dict[int, pd.Series] = {}
    for i, col in enumerate(result.columns):
        if result[col].dtype == object or pd.api.types.is_string_dtype(result[col]):
            nan_masks[i] = result[col].isna()

    # Clean column names
    result.columns = [
        col.strip() if isinstance(col, str) else col
        for col in result.columns
    ]

    # Clean string values
    for i, col in enumerate(result.columns):
        if i not in nan_masks:
            continue
        result[col] = (
            result[col]
            .astype(str)
            .str.strip()
            .str.replace(r"\s+", " ", regex=True)
        )
        # Restore NaN where original was NaN
        result.loc[nan_masks[i], col] = np.nan
    return result


def remove_empty_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Drop rows where every value is NaN or empty string."""
    mask = df.apply(
        lambda row: row.map(
            lambda v: pd.isna(v) or (isinstance(v, str) and v.strip() == "")
        ).all(),
        axis=1,
    )
    return df[~mask].reset_index(drop=True)


def remove_empty_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Drop columns where every value is NaN or empty string."""
    cols_to_keep = []
    for col in df.columns:
        series = df[col]
        all_empty = series.apply(
            lambda v: pd.isna(v) or (isinstance(v, str) and v.strip() == "")
        ).all()
        if not all_empty:
            cols_to_keep.append(col)
    return df[cols_to_keep].copy()


def remove_duplicates(
    df: pd.DataFrame,
    subset: list[str] | None = None,
    keep: Literal["first", "last", False] = "first",
) -> pd.DataFrame:
    """Remove duplicate rows."""
    return df.drop_duplicates(subset=subset, keep=keep).reset_index(drop=True)


# ── Column operations ──────────────────────────────────────────────


def remove_columns(
    df: pd.DataFrame, columns: list[str]
) -> pd.DataFrame:
    """Drop specified columns from the DataFrame."""
    existing = [c for c in columns if c in df.columns]
    return df.drop(columns=existing)


def rename_columns(
    df: pd.DataFrame, mapping: dict[str, str]
) -> pd.DataFrame:
    """Rename columns using a ``{old: new}`` mapping."""
    valid = {k: v for k, v in mapping.items() if k in df.columns}
    return df.rename(columns=valid)


def reorder_columns(
    df: pd.DataFrame, order: list[str]
) -> pd.DataFrame:
    """Reorder columns.  Columns not in *order* are appended at the end."""
    valid = [c for c in order if c in df.columns]
    remaining = [c for c in df.columns if c not in valid]
    return df[valid + remaining]


# ── Missing values ─────────────────────────────────────────────────


def fill_missing(
    df: pd.DataFrame,
    column: str,
    strategy: Literal[
        "value", "mean", "median", "mode", "forward", "backward", "drop"
    ] = "value",
    value: Any = None,
) -> pd.DataFrame:
    """Fill or drop missing values in a single column.

    Strategies:
    - ``value``   — replace NaN with *value*
    - ``mean``    — numeric mean
    - ``median``  — numeric median
    - ``mode``    — most frequent value
    - ``forward`` — forward-fill
    - ``backward``— backward-fill
    - ``drop``    — drop rows with NaN in this column
    """
    if column not in df.columns:
        return df.copy()

    result = df.copy()
    col = result[column]

    if strategy == "drop":
        return result.dropna(subset=[column]).reset_index(drop=True)
    elif strategy == "value":
        fill = value if value is not None else ""
    elif strategy == "mean":
        numeric = pd.to_numeric(col, errors="coerce")
        fill = numeric.mean()
    elif strategy == "median":
        numeric = pd.to_numeric(col, errors="coerce")
        fill = numeric.median()
    elif strategy == "mode":
        modes = col.mode()
        fill = modes.iloc[0] if len(modes) > 0 else ""
    elif strategy == "forward":
        result[column] = col.ffill()
        return result
    elif strategy == "backward":
        result[column] = col.bfill()
        return result
    else:
        return result

    result[column] = col.fillna(fill)
    return result


# ── Type normalisation ─────────────────────────────────────────────


def normalize_dates(
    df: pd.DataFrame,
    column: str,
    output_format: str = "%Y-%m-%d",
) -> pd.DataFrame:
    """Parse mixed date formats and normalise to a consistent format.

    Handles: ``MM/DD/YYYY``, ``DD-MM-YYYY``, ``YYYY.MM.DD``,
    ``Jan 5, 2024``, ISO-8601, and many more via pandas ``dayfirst``
    heuristic.
    """
    if column not in df.columns:
        return df.copy()

    result = df.copy()
    parsed = pd.to_datetime(result[column], errors="coerce", dayfirst=False)

    # For values that failed, try dayfirst=True
    failed_mask = parsed.isna() & result[column].notna()
    if failed_mask.any():
        retry = pd.to_datetime(
            result.loc[failed_mask, column],
            errors="coerce",
            dayfirst=True,
        )
        parsed = parsed.fillna(retry)

    # Format as string
    result[column] = parsed.dt.strftime(output_format)
    # Restore NaN where original was NaN or unparseable
    result.loc[parsed.isna(), column] = np.nan
    return result


def normalize_numbers(
    df: pd.DataFrame,
    column: str,
) -> pd.DataFrame:
    """Strip currency symbols, commas, and whitespace then convert to float.

    Handles: ``$1,234.56``, ``€ 1.234,56``, ``1 234.56``, ``(100)``
    (negative in accounting notation).
    """
    if column not in df.columns:
        return df.copy()

    result = df.copy()

    def _clean_number(val: Any) -> Any:
        if pd.isna(val):
            return np.nan
        s = str(val).strip()
        if not s:
            return np.nan

        # Handle accounting negatives: (100) → -100
        negative = False
        if s.startswith("(") and s.endswith(")"):
            s = s[1:-1]
            negative = True

        # Remove currency symbols and whitespace
        s = re.sub(r"[£$€¥₹₽\s]", "", s)

        # Detect European format: 1.234,56 → 1234.56
        if re.match(r"^\d{1,3}(\.\d{3})+(,\d+)?$", s):
            s = s.replace(".", "").replace(",", ".")
        else:
            # Standard: remove commas
            s = s.replace(",", "")

        # Handle percentage
        is_pct = s.endswith("%")
        if is_pct:
            s = s[:-1]

        try:
            num = float(s)
            if negative:
                num = -num
            if is_pct:
                num = num / 100.0
            return num
        except (ValueError, TypeError):
            return np.nan

    result[column] = result[column].map(_clean_number)
    return result


def normalize_booleans(
    df: pd.DataFrame,
    column: str,
) -> pd.DataFrame:
    """Map common boolean representations to ``True`` / ``False``.

    Recognises: ``yes``, ``no``, ``true``, ``false``, ``1``, ``0``,
    ``y``, ``n``, ``on``, ``off``, ``active``, ``inactive``.
    """
    if column not in df.columns:
        return df.copy()

    _TRUE = {"yes", "y", "true", "t", "1", "1.0", "on", "active", "enabled"}
    _FALSE = {"no", "n", "false", "f", "0", "0.0", "off", "inactive", "disabled"}

    result = df.copy()

    def _to_bool(val: Any) -> Any:
        if pd.isna(val):
            return np.nan
        s = str(val).strip().lower()
        if s in _TRUE:
            return True
        if s in _FALSE:
            return False
        return np.nan

    result[column] = result[column].map(_to_bool)
    return result


# ── Filtering ──────────────────────────────────────────────────────


def filter_rows(
    df: pd.DataFrame,
    column: str,
    operator: Literal["==", "!=", ">", "<", ">=", "<=", "contains", "not_contains"],
    value: Any,
) -> pd.DataFrame:
    """Filter rows by a condition on a single column."""
    if column not in df.columns:
        return df.copy()

    col = df[column]

    if operator == "==":
        mask = col == value
    elif operator == "!=":
        mask = col != value
    elif operator == ">":
        mask = pd.to_numeric(col, errors="coerce") > float(value)
    elif operator == "<":
        mask = pd.to_numeric(col, errors="coerce") < float(value)
    elif operator == ">=":
        mask = pd.to_numeric(col, errors="coerce") >= float(value)
    elif operator == "<=":
        mask = pd.to_numeric(col, errors="coerce") <= float(value)
    elif operator == "contains":
        mask = col.astype(str).str.contains(str(value), case=False, na=False)
    elif operator == "not_contains":
        mask = ~col.astype(str).str.contains(str(value), case=False, na=False)
    else:
        return df.copy()

    return df[mask].reset_index(drop=True)


def replace_values(
    df: pd.DataFrame,
    column: str,
    old_value: str,
    new_value: str,
    regex: bool = False,
) -> pd.DataFrame:
    """Replace occurrences of *old_value* with *new_value* in a column."""
    if column not in df.columns:
        return df.copy()

    result = df.copy()
    result[column] = (
        result[column]
        .astype(str)
        .str.replace(old_value, new_value, regex=regex)
    )
    # Restore NaN
    result.loc[df[column].isna(), column] = np.nan
    return result


# ── Privacy / PII transforms ──────────────────────────────────────


def mask_column(
    df: pd.DataFrame,
    column: str,
    mask_char: str = "*",
    show_last: int = 4,
) -> pd.DataFrame:
    """Mask column values, optionally showing the last N characters.

    Example: ``alice@example.com`` → ``*************com``
    """
    if column not in df.columns:
        return df.copy()

    result = df.copy()

    def _mask(val: Any) -> Any:
        if pd.isna(val):
            return np.nan
        s = str(val)
        if len(s) <= show_last:
            return mask_char * len(s)
        return mask_char * (len(s) - show_last) + s[-show_last:]

    result[column] = result[column].map(_mask)
    return result


def redact_column(
    df: pd.DataFrame,
    column: str,
    replacement: str = "[REDACTED]",
) -> pd.DataFrame:
    """Replace all non-NaN values in a column with *replacement*."""
    if column not in df.columns:
        return df.copy()

    result = df.copy()
    result.loc[result[column].notna(), column] = replacement
    return result


def hash_column(
    df: pd.DataFrame,
    column: str,
    algorithm: str = "sha256",
    salt: str = "",
) -> pd.DataFrame:
    """Hash column values using the specified algorithm.

    The hash is deterministic: same input → same hash within a run.
    Adding a salt makes it harder to reverse via rainbow tables.
    """
    if column not in df.columns:
        return df.copy()

    result = df.copy()

    def _hash(val: Any) -> Any:
        if pd.isna(val):
            return np.nan
        s = salt + str(val)
        return hashlib.new(algorithm, s.encode("utf-8")).hexdigest()

    result[column] = result[column].map(_hash)
    return result


def pseudonymize_column(
    df: pd.DataFrame,
    column: str,
    prefix: str = "ENTITY",
    seed: int = 42,
) -> pd.DataFrame:
    """Replace values with consistent pseudonyms.

    Same input value → same pseudonym within a run.
    Example: ``Alice`` → ``ENTITY_001``, ``Bob`` → ``ENTITY_002``
    """
    if column not in df.columns:
        return df.copy()

    result = df.copy()
    unique_vals = result[column].dropna().unique()

    # Deterministic shuffle using seed
    rng = np.random.default_rng(seed)
    indices = rng.permutation(len(unique_vals))
    mapping = {
        val: f"{prefix}_{idx + 1:04d}"
        for idx, val in zip(indices, unique_vals)
    }

    def _pseudo(val: Any) -> Any:
        if pd.isna(val):
            return np.nan
        return mapping.get(val, f"{prefix}_UNKNOWN")

    result[column] = result[column].map(_pseudo)
    return result


# ── Statistical privacy ───────────────────────────────────────────


def generalize_column(
    df: pd.DataFrame,
    column: str,
    bins: list[float] | int = 5,
    labels: list[str] | None = None,
) -> pd.DataFrame:
    """Bin numeric values into ranges (generalisation).

    Parameters
    ----------
    bins
        Either an integer (number of equal-width bins) or a list of
        bin edges.
    labels
        Optional labels for the bins.  Must be ``len(bins) - 1`` if
        *bins* is a list.
    """
    if column not in df.columns:
        return df.copy()

    result = df.copy()
    numeric = pd.to_numeric(result[column], errors="coerce")

    if isinstance(bins, int):
        result[column] = pd.cut(
            numeric, bins=bins, labels=labels, include_lowest=True
        ).astype(str)
    else:
        result[column] = pd.cut(
            numeric,
            bins=bins,
            labels=labels,
            include_lowest=True,
        ).astype(str)

    # Restore NaN
    result.loc[numeric.isna(), column] = np.nan
    return result


def revenue_bands(
    df: pd.DataFrame,
    column: str,
) -> pd.DataFrame:
    """Categorise revenue values into standard bands.

    Bands: ``<10K``, ``10K–50K``, ``50K–100K``, ``100K–500K``,
    ``500K–1M``, ``1M+``
    """
    if column not in df.columns:
        return df.copy()

    result = df.copy()
    numeric = pd.to_numeric(result[column], errors="coerce")

    edges = [float("-inf"), 10_000, 50_000, 100_000, 500_000, 1_000_000, float("inf")]
    band_labels = ["<10K", "10K–50K", "50K–100K", "100K–500K", "500K–1M", "1M+"]

    result[column] = pd.cut(
        numeric, bins=edges, labels=band_labels, include_lowest=True
    ).astype(str)
    result.loc[numeric.isna(), column] = np.nan
    return result


def suppress_low_counts(
    df: pd.DataFrame,
    group_column: str,
    threshold: int = 5,
    replacement: str = "[SUPPRESSED]",
) -> pd.DataFrame:
    """Replace group values that appear fewer than *threshold* times.

    This prevents re-identification of rare individuals in aggregated data.
    """
    if group_column not in df.columns:
        return df.copy()

    result = df.copy()
    counts = result[group_column].value_counts()
    low_count_vals = counts[counts < threshold].index
    result.loc[
        result[group_column].isin(low_count_vals), group_column
    ] = replacement
    return result


# ── Metadata ───────────────────────────────────────────────────────


def strip_metadata_from_xlsx(path: str) -> dict[str, str | None]:
    """Remove workbook-level metadata from an XLSX file.

    Strips: author, title, subject, description, keywords, category,
    last_modified_by, company.

    Returns a dict of what was removed.

    **This modifies the file in-place** — call only on the output copy.
    """
    from openpyxl import load_workbook

    wb = load_workbook(path)
    props = wb.properties
    removed: dict[str, str | None] = {}

    for attr in (
        "creator", "title", "subject", "description",
        "keywords", "category", "lastModifiedBy",
    ):
        old_val = getattr(props, attr, None)
        if old_val:
            removed[attr] = old_val
            setattr(props, attr, "")

    # Clear company from extended properties if present
    if hasattr(wb, "extended_properties"):
        ext = wb.extended_properties
        if hasattr(ext, "company") and ext.company:
            removed["company"] = ext.company
            ext.company = ""

    wb.save(path)
    wb.close()
    return removed
