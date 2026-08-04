"""Tests for processing.pipeline module."""

from __future__ import annotations

import pandas as pd
import numpy as np
import pytest

from deskx.processing.pipeline import (
    PipelineResult,
    TransformStep,
    TransformType,
    execute_pipeline,
)


@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "  Name  ": ["  Alice  ", " Bob ", "Charlie", np.nan, "Alice"],
        "Email": [
            "alice@test.com", "bob@test.com", "charlie@test.com",
            np.nan, "alice@test.com",
        ],
        "Salary": ["$75,000", "$62,500", "$85,000", "$55,000", "$75,000"],
        "Active": ["Yes", "No", "true", "0", "Yes"],
        "Empty": [np.nan, np.nan, np.nan, np.nan, np.nan],
    })


class TestPipelineExecution:
    def test_empty_pipeline(self, sample_df):
        result_df, result = execute_pipeline(sample_df, [])
        assert result.total_rows_before == len(sample_df)
        assert result.total_rows_after == len(sample_df)
        assert len(result.steps) == 0

    def test_single_step(self, sample_df):
        steps = [TransformStep(TransformType.TRIM_WHITESPACE)]
        result_df, result = execute_pipeline(sample_df, steps)
        assert "Name" in result_df.columns  # Column name trimmed
        assert len(result.steps) == 1
        assert result.steps[0].success

    def test_multi_step_pipeline(self, sample_df):
        steps = [
            TransformStep(TransformType.TRIM_WHITESPACE),
            TransformStep(TransformType.REMOVE_EMPTY_COLUMNS),
            TransformStep(TransformType.REMOVE_DUPLICATES),
        ]
        result_df, result = execute_pipeline(sample_df, steps)
        assert len(result.steps) == 3
        assert all(s.success for s in result.steps)
        assert "Empty" not in result_df.columns
        # Duplicates removed
        assert len(result_df) < len(sample_df)

    def test_disabled_step_skipped(self, sample_df):
        steps = [
            TransformStep(TransformType.TRIM_WHITESPACE, enabled=True),
            TransformStep(TransformType.REMOVE_EMPTY_COLUMNS, enabled=False),
        ]
        result_df, result = execute_pipeline(sample_df, steps)
        assert len(result.steps) == 1  # Disabled step not recorded
        assert "Empty" in result_df.columns  # Column still there

    def test_step_with_params(self, sample_df):
        steps = [
            TransformStep(
                TransformType.NORMALIZE_NUMBERS,
                params={"column": "Salary"},
            ),
        ]
        result_df, result = execute_pipeline(sample_df, steps)
        assert result.steps[0].success
        assert result_df["Salary"].iloc[0] == 75000.0

    def test_failed_step_continues(self, sample_df):
        steps = [
            TransformStep(
                TransformType.NORMALIZE_NUMBERS,
                params={"column": "NonexistentColumn"},
            ),
            TransformStep(TransformType.TRIM_WHITESPACE),
        ]
        result_df, result = execute_pipeline(sample_df, steps)
        # First step should succeed but not do anything (column doesn't exist)
        # Second step should succeed
        assert len(result.steps) == 2
        assert result.steps[1].success

    def test_result_summary(self, sample_df):
        steps = [TransformStep(TransformType.REMOVE_EMPTY_COLUMNS)]
        _, result = execute_pipeline(sample_df, steps)
        summary = result.summary_text()
        assert "Pipeline Summary" in summary
        assert "Columns:" in summary

    def test_privacy_pipeline(self, sample_df):
        steps = [
            TransformStep(
                TransformType.MASK_COLUMN,
                params={"column": "Email", "show_last": 4},
            ),
            TransformStep(
                TransformType.REDACT_COLUMN,
                params={"column": "Salary"},
            ),
        ]
        result_df, result = execute_pipeline(sample_df, steps)
        assert result_df["Email"].iloc[0].endswith(".com")
        assert result_df["Email"].iloc[0].startswith("*")
        assert result_df["Salary"].iloc[0] == "[REDACTED]"
