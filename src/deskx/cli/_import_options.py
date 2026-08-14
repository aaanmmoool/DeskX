"""Import-option helpers for the CLI (header row, sheets).

These only choose kwargs for the existing adapters — they do not
re-implement CSV/Excel reading.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from deskx.adapters.adapter_registry import AdapterRegistry
from deskx.adapters.xlsx_adapter import XlsxAdapter


def guess_header_row(
    path: Path,
    *,
    registry: AdapterRegistry,
    sheet_name: str | int = 0,
    max_scan: int = 40,
) -> int:
    """Return the most likely 0-based header row for tabular files.

    Spreadsheets often put a title banner above the real column names.
    DeskX's GUI lets users pick that row; the CLI uses this heuristic
    when ``--header-row`` is omitted.
    """
    suffix = path.suffix.lower()
    if suffix not in {".xlsx", ".csv", ".txt"}:
        return 0

    try:
        raw = _read_raw_grid(path, registry, sheet_name=sheet_name, max_scan=max_scan)
    except Exception:
        return 0

    if raw.empty:
        return 0

    best_row = 0
    best_score = -1.0
    for index in range(min(len(raw), max_scan)):
        score = _header_score(raw.iloc[index])
        if score > best_score:
            best_score = score
            best_row = index

    # Prefer row 0 when nothing looks like a header strip.
    if best_score < 1.5:
        return 0
    return best_row


def resolve_import_kwargs(
    path: Path,
    *,
    registry: AdapterRegistry,
    sheet: str | None = None,
    header_row: int | None = None,
) -> dict[str, Any]:
    """Build adapter kwargs, guessing the header row when needed."""
    kwargs: dict[str, Any] = {}
    adapter = registry.get(path.suffix)

    if isinstance(adapter, XlsxAdapter):
        sheets = adapter.get_sheet_names(path)
        if sheet:
            if sheet not in sheets:
                raise ValueError(
                    f"Worksheet '{sheet}' not found. Available: {', '.join(sheets)}"
                )
            kwargs["sheet_name"] = sheet
        elif sheets:
            kwargs["sheet_name"] = sheets[0]

    if header_row is not None:
        kwargs["header_row"] = header_row
    else:
        kwargs["header_row"] = guess_header_row(
            path,
            registry=registry,
            sheet_name=kwargs.get("sheet_name", 0),
        )
    return kwargs


def _read_raw_grid(
    path: Path,
    registry: AdapterRegistry,
    *,
    sheet_name: str | int,
    max_scan: int,
) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".xlsx":
        return pd.read_excel(
            path,
            engine="openpyxl",
            sheet_name=sheet_name,
            header=None,
            nrows=max_scan,
        )
    if suffix == ".csv":
        try:
            return pd.read_csv(path, header=None, nrows=max_scan)
        except UnicodeDecodeError:
            return pd.read_csv(
                path, header=None, nrows=max_scan, encoding="latin-1"
            )
    adapter = registry.get(suffix)
    delimiter = "\t"
    if hasattr(adapter, "detect_delimiter"):
        detected = adapter.detect_delimiter(path)
        if detected:
            delimiter = detected
    return pd.read_csv(
        path, sep=delimiter, header=None, nrows=max_scan, engine="python"
    )


def _header_score(row: pd.Series) -> float:
    values = [v for v in row.tolist() if not _is_blank(v)]
    if len(values) < 2:
        return 0.0

    score = 0.0
    seen: set[str] = set()
    for value in values:
        text = str(value).strip()
        if not text:
            continue
        lowered = text.casefold()
        if lowered in seen:
            score -= 0.5
        seen.add(lowered)

        if _looks_numeric(text) or _looks_date(text):
            score -= 0.8
            continue
        if text.lower().startswith("unnamed"):
            score -= 1.0
            continue
        if any(ch.isalpha() for ch in text):
            score += 1.2
            if " " in text or "_" in text or "-" in text:
                score += 0.2
        else:
            score -= 0.3
    return score


def _is_blank(value: Any) -> bool:
    if value is None:
        return True
    try:
        if pd.isna(value):
            return True
    except (TypeError, ValueError):
        pass
    return str(value).strip() == ""


def _looks_numeric(text: str) -> bool:
    cleaned = text.replace(",", "").replace("%", "").strip()
    try:
        float(cleaned)
        return True
    except ValueError:
        return False


def _looks_date(text: str) -> bool:
    sample = str(text).strip()
    if sample.count("-") >= 2 or sample.count("/") >= 2:
        try:
            pd.to_datetime(sample, errors="raise")
            return True
        except Exception:
            return False
    return False
