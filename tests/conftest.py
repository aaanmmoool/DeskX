"""Shared test fixtures and helpers."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

# ── Fixture paths ───────────────────────────────────────────────────

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
    """Return the path to the test fixtures directory."""
    return FIXTURES_DIR


@pytest.fixture
def sample_csv(fixtures_dir: Path) -> Path:
    return fixtures_dir / "sample.csv"


@pytest.fixture
def sample_json(fixtures_dir: Path) -> Path:
    return fixtures_dir / "sample.json"


@pytest.fixture
def sample_xlsx(fixtures_dir: Path) -> Path:
    return fixtures_dir / "sample.xlsx"


@pytest.fixture
def sample_txt(fixtures_dir: Path) -> Path:
    return fixtures_dir / "sample.txt"


@pytest.fixture
def sample_df() -> pd.DataFrame:
    """A small DataFrame for adapter round-trip tests."""
    return pd.DataFrame({
        "id": [1, 2, 3, 4, 5],
        "name": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
        "email": [
            "alice@example.com",
            "bob@example.com",
            "charlie@example.com",
            "diana@example.com",
            "eve@example.com",
        ],
        "age": [30, 25, 35, 28, 32],
        "salary": [50000.0, 60000.0, 75000.0, 55000.0, 80000.0],
    })


@pytest.fixture
def tmp_output_dir(tmp_path: Path) -> Path:
    """A temporary directory for output files."""
    out = tmp_path / "output"
    out.mkdir()
    return out
