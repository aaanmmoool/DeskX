"""Pure helpers for the interactive sanitize workflow.

No terminal I/O here — only mappings onto the existing detector,
transform types, and :class:`~deskx.processing.pipeline.TransformStep`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from deskx.processing.pipeline import TransformStep, TransformType
from deskx.processing.sensitive_detector import SensitiveColumn
from deskx.processing.transform_catalog import TRANSFORM_CATALOG

# Actions exposed in the interactive sanitize menu.  These map 1:1 onto
# transforms that already exist in the processing engine.
SANITIZE_ACTIONS: tuple[tuple[str, str, TransformType | None], ...] = (
    ("1", "Mask", TransformType.MASK_COLUMN),
    ("2", "Redact", TransformType.REDACT_COLUMN),
    ("3", "Hash", TransformType.HASH_COLUMN),
    ("4", "Pseudonymize", TransformType.PSEUDONYMIZE_COLUMN),
    ("5", "Remove", TransformType.REMOVE_COLUMNS),
    ("6", "Skip", None),
)

_CATEGORY_LABELS = {
    "email": "Email",
    "phone": "Phone Number",
    "ssn": "National ID / SSN",
    "name": "Name",
    "address": "Address",
    "dob": "Date of Birth",
    "financial": "Financial",
    "identifier": "Identifier",
    "ip_address": "IP Address",
    "credential": "Credential",
    "credit_card": "Credit Card",
}


@dataclass
class ColumnChoice:
    """User-selected sanitization for one detected column."""

    column: str
    category: str
    action_label: str
    transform_type: TransformType | None
    params: dict[str, Any] = field(default_factory=dict)
    example_before: str = ""
    example_after: str = ""

    @property
    def configured(self) -> bool:
        return self.transform_type is not None

    def to_step(self) -> TransformStep | None:
        if self.transform_type is None:
            return None
        return TransformStep(
            transform_type=self.transform_type,
            params=dict(self.params),
            enabled=True,
        )


def confidence_label(score: float) -> str:
    if score >= 0.75:
        return "High"
    if score >= 0.5:
        return "Medium"
    return "Low"


def category_label(category: str) -> str:
    return _CATEGORY_LABELS.get(category, category.replace("_", " ").title())


def action_for_key(key: str) -> tuple[str, TransformType | None] | None:
    for option, label, transform in SANITIZE_ACTIONS:
        if option == key:
            return label, transform
    return None


def default_params(
    transform_type: TransformType,
    column: str,
    *,
    show_last: int = 4,
    replacement: str = "[REDACTED]",
    prefix: str = "Person_",
) -> dict[str, Any]:
    """Build engine params matching GUI defaults where they exist."""
    if transform_type is TransformType.MASK_COLUMN:
        return {"column": column, "mask_char": "*", "show_last": show_last}
    if transform_type is TransformType.REDACT_COLUMN:
        return {"column": column, "replacement": replacement}
    if transform_type is TransformType.HASH_COLUMN:
        return {"column": column, "algorithm": "sha256", "salt": ""}
    if transform_type is TransformType.PSEUDONYMIZE_COLUMN:
        return {"column": column, "prefix": prefix, "seed": 42}
    if transform_type is TransformType.REMOVE_COLUMNS:
        return {"columns": [column]}
    return {"column": column}


def synthetic_example(
    transform_type: TransformType | None,
    category: str,
    params: dict[str, Any] | None = None,
) -> tuple[str, str]:
    """Return a static before/after pair — never real dataset values."""
    params = params or {}
    samples = {
        "email": "john.doe@example.com",
        "phone": "+1-555-0100",
        "ssn": "123-45-6789",
        "name": "Ada Lovelace",
        "address": "221B Baker Street",
        "dob": "1990-04-12",
        "financial": "85000",
        "identifier": "CUST-10042",
        "ip_address": "192.168.1.10",
        "credential": "s3cret!",
        "credit_card": "4111-1111-1111-1111",
    }
    before = samples.get(category, "sample-value")

    if transform_type is None:
        return before, before
    if transform_type is TransformType.MASK_COLUMN:
        show_last = int(params.get("show_last", 4))
        mask_char = str(params.get("mask_char", "*"))
        if len(before) <= show_last:
            after = mask_char * len(before)
        else:
            after = mask_char * (len(before) - show_last) + before[-show_last:]
        return before, after
    if transform_type is TransformType.REDACT_COLUMN:
        return before, str(params.get("replacement", "[REDACTED]"))
    if transform_type is TransformType.HASH_COLUMN:
        return before, "a3f1… (SHA-256 fingerprint)"
    if transform_type is TransformType.PSEUDONYMIZE_COLUMN:
        prefix = str(params.get("prefix", "Person_"))
        return before, f"{prefix}001"
    if transform_type is TransformType.REMOVE_COLUMNS:
        return before, "(column removed)"
    meta = TRANSFORM_CATALOG.get(transform_type)
    return before, meta.example_out if meta else "(transformed)"


def choices_to_steps(choices: dict[str, ColumnChoice]) -> list[TransformStep]:
    steps: list[TransformStep] = []
    for choice in choices.values():
        step = choice.to_step()
        if step is not None:
            steps.append(step)
    return steps


def summarize_detection(detected: list[SensitiveColumn]) -> str:
    count = len(detected)
    noun = "column" if count == 1 else "columns"
    return f"Detected {count} sensitive {noun}"
