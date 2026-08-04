"""Heuristic-based sensitive data detection.

Scans column names and sample values to estimate whether a column
contains personally identifiable information (PII) or sensitive data.

Returns per-column confidence scores and suggested sanitisation actions.

This module has **no PySide6 dependency**.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

import pandas as pd


# ── Detection result ───────────────────────────────────────────────


@dataclass
class SensitiveColumn:
    """Detection result for a single column."""

    column_name: str
    category: str  # e.g. "email", "phone", "name", "financial"
    confidence: float  # 0.0 – 1.0
    reason: str  # human-readable explanation
    suggested_action: str  # "mask", "redact", "hash", "pseudonymize", "ignore"
    sample_matches: list[str] = field(default_factory=list)


# ── Column name patterns ──────────────────────────────────────────

# (regex_pattern, category, confidence_boost, suggested_action)
_NAME_PATTERNS: list[tuple[str, str, float, str]] = [
    # Email
    (r"(?i)\b(e[-_]?mail|email[-_]?addr)\b", "email", 0.85, "mask"),
    # Phone
    (r"(?i)\b(phone|tel|mobile|cell|fax|contact[-_]?num)\b", "phone", 0.80, "mask"),
    # SSN / National ID
    (r"(?i)\b(ssn|social[-_]?sec|national[-_]?id|sin|nino|tax[-_]?id)\b", "ssn", 0.95, "hash"),
    # Name
    (r"(?i)\b(first[-_]?name|last[-_]?name|full[-_]?name|surname|given[-_]?name)\b", "name", 0.80, "pseudonymize"),
    (r"(?i)^name$", "name", 0.70, "pseudonymize"),
    # Address
    (r"(?i)\b(address|street|city|state|zip[-_]?code|postal[-_]?code|country)\b", "address", 0.75, "redact"),
    # Date of birth
    (r"(?i)\b(dob|date[-_]?of[-_]?birth|birth[-_]?date|birthday)\b", "dob", 0.85, "generalize"),
    # Financial
    (r"(?i)\b(salary|income|revenue|wage|pay|compensation|credit[-_]?card|card[-_]?num|account[-_]?num|bank)\b", "financial", 0.80, "mask"),
    # ID fields
    (r"(?i)\b(employee[-_]?id|customer[-_]?id|user[-_]?id|patient[-_]?id|member[-_]?id|passport)\b", "identifier", 0.70, "hash"),
    # IP address
    (r"(?i)\b(ip[-_]?addr|ip[-_]?address)\b", "ip_address", 0.80, "mask"),
    # Password
    (r"(?i)\b(password|passwd|pwd|secret|token|api[-_]?key)\b", "credential", 0.95, "redact"),
]


# ── Value patterns ────────────────────────────────────────────────

_EMAIL_RE = re.compile(
    r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
)
_PHONE_RE = re.compile(
    r"^[\+]?[\d\s\-\.\(\)]{7,18}$"
)
_SSN_RE = re.compile(
    r"^\d{3}[-\s]?\d{2}[-\s]?\d{4}$"
)
_CREDIT_CARD_RE = re.compile(
    r"^\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}$"
)
_IP_RE = re.compile(
    r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$"
)
_ZIP_RE = re.compile(
    r"^\d{5}(-\d{4})?$"
)


def _value_match_rate(
    series: pd.Series, pattern: re.Pattern[str], sample_size: int = 100
) -> tuple[float, list[str]]:
    """Return (match_fraction, sample_matches) for non-null values."""
    non_null = series.dropna().astype(str)
    if len(non_null) == 0:
        return 0.0, []

    sample = non_null.head(sample_size)
    matches = [v for v in sample if pattern.match(v.strip())]
    rate = len(matches) / len(sample)
    return rate, matches[:5]


# ── Main detection function ───────────────────────────────────────


def detect_sensitive_columns(
    df: pd.DataFrame,
    sample_size: int = 200,
    min_confidence: float = 0.3,
) -> list[SensitiveColumn]:
    """Scan a DataFrame for columns likely containing sensitive data.

    Parameters
    ----------
    df
        The DataFrame to scan.
    sample_size
        How many rows to sample for value-pattern matching.
    min_confidence
        Minimum confidence to include in results.

    Returns
    -------
    list[SensitiveColumn]
        Ordered by confidence (highest first).
    """
    results: list[SensitiveColumn] = []

    for col in df.columns:
        col_str = str(col)
        best: SensitiveColumn | None = None

        # ── Check column name patterns ──────────────────────────
        for pattern, category, conf, action in _NAME_PATTERNS:
            if re.search(pattern, col_str):
                candidate = SensitiveColumn(
                    column_name=col_str,
                    category=category,
                    confidence=conf,
                    reason=f"Column name matches '{category}' pattern",
                    suggested_action=action,
                )
                if best is None or candidate.confidence > best.confidence:
                    best = candidate

        # ── Check value patterns ────────────────────────────────
        series = df[col].dropna().astype(str).head(sample_size)
        if len(series) == 0:
            if best and best.confidence >= min_confidence:
                results.append(best)
            continue

        value_checks: list[tuple[re.Pattern[str], str, float, str]] = [
            (_EMAIL_RE, "email", 0.90, "mask"),
            (_PHONE_RE, "phone", 0.60, "mask"),
            (_SSN_RE, "ssn", 0.95, "hash"),
            (_CREDIT_CARD_RE, "credit_card", 0.95, "redact"),
            (_IP_RE, "ip_address", 0.75, "mask"),
        ]

        for vpattern, vcategory, vconf_max, vaction in value_checks:
            rate, samples = _value_match_rate(series, vpattern, sample_size)
            if rate >= 0.5:
                # High match rate → high confidence
                vconf = min(rate * vconf_max, 0.99)
                candidate = SensitiveColumn(
                    column_name=col_str,
                    category=vcategory,
                    confidence=vconf,
                    reason=(
                        f"{rate:.0%} of values match {vcategory} pattern"
                    ),
                    suggested_action=vaction,
                    sample_matches=samples,
                )
                if best is None or candidate.confidence > best.confidence:
                    best = candidate

        # ── Boost confidence if both name and value match ───────
        if best is not None:
            if best.confidence >= min_confidence:
                results.append(best)

    # Sort by confidence descending
    results.sort(key=lambda r: r.confidence, reverse=True)
    return results
