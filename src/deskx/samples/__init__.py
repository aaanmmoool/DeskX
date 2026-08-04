"""Bundled sample datasets for DeskX first-run testing and demos."""

from __future__ import annotations

from pathlib import Path

SAMPLES_DIR = Path(__file__).parent


def get_sample_employee_dataset_path() -> Path:
    """Return the absolute Path to sample_employees.csv."""
    return SAMPLES_DIR / "sample_employees.csv"
