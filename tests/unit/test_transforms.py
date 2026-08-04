"""Tests for processing.transforms module."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from deskx.processing.transforms import (
    fill_missing,
    filter_rows,
    generalize_column,
    hash_column,
    mask_column,
    normalize_booleans,
    normalize_dates,
    normalize_numbers,
    pseudonymize_column,
    redact_column,
    remove_columns,
    remove_duplicates,
    remove_empty_columns,
    remove_empty_rows,
    rename_columns,
    reorder_columns,
    replace_values,
    revenue_bands,
    suppress_low_counts,
    trim_whitespace,
)


# ── Fixtures ────────────────────────────────────────────────────────


@pytest.fixture
def messy_df():
    """A DataFrame with realistic data quality issues."""
    return pd.DataFrame(
        {
            "  Name  ": ["  Alice  ", " Bob", "Charlie ", np.nan, ""],
            "Email": [
                "alice@test.com",
                "bob@test.com",
                np.nan,
                "diana@test.com",
                "eve@test.com",
            ],
            "Salary": [
                "$75,000.00",
                "€62,500",
                "85000",
                "(45,000)",
                "  $110,000  ",
            ],
            "DoB": [
                "01/15/1990",
                "1985-03-22",
                "22-07-1992",
                "Mar 5, 1988",
                "1995.11.30",
            ],
            "Active": ["Yes", "true", "1", "No", "0"],
            "Empty": [np.nan, np.nan, np.nan, np.nan, np.nan],
            "Department": ["Eng", "Mkt", "Eng", "HR", "Eng"],
        }
    )


# ── Cleaning tests ──────────────────────────────────────────────────


class TestTrimWhitespace:
    def test_strips_values(self, messy_df):
        result = trim_whitespace(messy_df)
        assert result["Name"].iloc[0] == "Alice"
        assert result["Name"].iloc[1] == "Bob"
        assert result["Name"].iloc[2] == "Charlie"

    def test_strips_column_names(self, messy_df):
        result = trim_whitespace(messy_df)
        assert "Name" in result.columns
        assert "  Name  " not in result.columns

    def test_preserves_nan(self, messy_df):
        result = trim_whitespace(messy_df)
        assert pd.isna(result["Name"].iloc[3])


class TestRemoveEmptyRows:
    def test_removes_all_nan_row(self):
        df = pd.DataFrame(
            {
                "a": [1, np.nan, 3],
                "b": ["x", np.nan, "z"],
            }
        )
        result = remove_empty_rows(df)
        assert len(result) == 2

    def test_removes_empty_string_row(self):
        df = pd.DataFrame({"a": ["hello", "", "world"], "b": ["x", "", "z"]})
        result = remove_empty_rows(df)
        assert len(result) == 2


class TestRemoveEmptyColumns:
    def test_drops_all_nan_column(self, messy_df):
        result = remove_empty_columns(messy_df)
        assert "Empty" not in result.columns

    def test_keeps_non_empty(self, messy_df):
        result = remove_empty_columns(messy_df)
        assert "Email" in result.columns


class TestRemoveDuplicates:
    def test_basic_dedup(self):
        df = pd.DataFrame({"a": [1, 2, 1, 3], "b": ["x", "y", "x", "z"]})
        result = remove_duplicates(df)
        assert len(result) == 3

    def test_keep_last(self):
        df = pd.DataFrame({"a": [1, 2, 1], "b": ["first", "mid", "last"]})
        result = remove_duplicates(df, subset=["a"], keep="last")
        vals = result["b"].tolist()
        assert "last" in vals
        assert "first" not in vals


# ── Column operation tests ──────────────────────────────────────────


class TestRemoveColumns:
    def test_removes_specified(self, messy_df):
        result = remove_columns(messy_df, ["Empty", "Active"])
        assert "Empty" not in result.columns
        assert "Active" not in result.columns

    def test_ignores_nonexistent(self, messy_df):
        result = remove_columns(messy_df, ["nonexistent"])
        assert len(result.columns) == len(messy_df.columns)


class TestRenameColumns:
    def test_renames(self, messy_df):
        result = rename_columns(messy_df, {"Email": "email_address"})
        assert "email_address" in result.columns
        assert "Email" not in result.columns


class TestReorderColumns:
    def test_reorders(self, messy_df):
        result = reorder_columns(messy_df, ["Email", "Department"])
        assert list(result.columns[:2]) == ["Email", "Department"]

    def test_appends_remaining(self, messy_df):
        result = reorder_columns(messy_df, ["Email"])
        assert result.columns[0] == "Email"
        assert len(result.columns) == len(messy_df.columns)


# ── Missing value tests ────────────────────────────────────────────


class TestFillMissing:
    def test_fill_with_value(self):
        df = pd.DataFrame({"a": [1, np.nan, 3]})
        result = fill_missing(df, "a", strategy="value", value=0)
        assert result["a"].iloc[1] == 0

    def test_fill_with_mean(self):
        df = pd.DataFrame({"a": [10.0, np.nan, 30.0]})
        result = fill_missing(df, "a", strategy="mean")
        assert result["a"].iloc[1] == 20.0

    def test_drop_rows(self):
        df = pd.DataFrame({"a": [1, np.nan, 3]})
        result = fill_missing(df, "a", strategy="drop")
        assert len(result) == 2


# ── Type normalisation tests ──────────────────────────────────────


class TestNormalizeDates:
    def test_mixed_formats(self, messy_df):
        result = normalize_dates(messy_df, "DoB")
        # All should be YYYY-MM-DD format
        assert result["DoB"].iloc[0] == "1990-01-15"
        assert result["DoB"].iloc[1] == "1985-03-22"


class TestNormalizeNumbers:
    def test_currency_symbols(self, messy_df):
        result = normalize_numbers(messy_df, "Salary")
        assert result["Salary"].iloc[0] == 75000.0

    def test_accounting_negative(self, messy_df):
        result = normalize_numbers(messy_df, "Salary")
        assert result["Salary"].iloc[3] == -45000.0

    def test_euro_format(self):
        df = pd.DataFrame({"val": ["1.234,56"]})
        result = normalize_numbers(df, "val")
        assert abs(result["val"].iloc[0] - 1234.56) < 0.01


class TestNormalizeBooleans:
    def test_common_values(self, messy_df):
        result = normalize_booleans(messy_df, "Active")
        assert result["Active"].iloc[0] == True  # "Yes"  # noqa: E712
        assert result["Active"].iloc[1] == True  # "true"  # noqa: E712
        assert result["Active"].iloc[2] == True  # "1"  # noqa: E712
        assert result["Active"].iloc[3] == False  # "No"  # noqa: E712
        assert result["Active"].iloc[4] == False  # "0"  # noqa: E712


# ── Filter tests ───────────────────────────────────────────────────


class TestFilterRows:
    def test_equals(self, messy_df):
        result = filter_rows(messy_df, "Department", "==", "Eng")
        assert len(result) == 3

    def test_contains(self, messy_df):
        result = filter_rows(messy_df, "Email", "contains", "test.com")
        assert len(result) == 4


class TestReplaceValues:
    def test_basic_replace(self):
        df = pd.DataFrame({"a": ["hello world", "hello there"]})
        result = replace_values(df, "a", "hello", "hi")
        assert result["a"].iloc[0] == "hi world"


# ── Privacy tests ──────────────────────────────────────────────────


class TestMaskColumn:
    def test_masks_with_last_4(self):
        df = pd.DataFrame({"email": ["alice@example.com"]})
        result = mask_column(df, "email", show_last=4)
        assert result["email"].iloc[0].endswith(".com")
        assert result["email"].iloc[0].startswith("*")


class TestRedactColumn:
    def test_replaces_all(self):
        df = pd.DataFrame({"ssn": ["123-45-6789", np.nan]})
        result = redact_column(df, "ssn")
        assert result["ssn"].iloc[0] == "[REDACTED]"
        assert pd.isna(result["ssn"].iloc[1])


class TestHashColumn:
    def test_deterministic(self):
        df = pd.DataFrame({"email": ["alice@test.com", "alice@test.com"]})
        result = hash_column(df, "email")
        assert result["email"].iloc[0] == result["email"].iloc[1]
        assert len(result["email"].iloc[0]) == 64  # SHA-256 hex

    def test_preserves_nan(self):
        df = pd.DataFrame({"val": ["hello", np.nan]})
        result = hash_column(df, "val")
        assert pd.isna(result["val"].iloc[1])


class TestPseudonymizeColumn:
    def test_consistent_mapping(self):
        df = pd.DataFrame({"name": ["Alice", "Bob", "Alice"]})
        result = pseudonymize_column(df, "name")
        # Same input → same pseudonym
        assert result["name"].iloc[0] == result["name"].iloc[2]
        assert result["name"].iloc[0] != result["name"].iloc[1]


# ── Statistical privacy tests ─────────────────────────────────────


class TestRevenueBands:
    def test_bands(self):
        df = pd.DataFrame({"revenue": [5000, 25000, 75000, 250000, 750000, 2000000]})
        result = revenue_bands(df, "revenue")
        assert result["revenue"].iloc[0] == "<10K"
        assert result["revenue"].iloc[5] == "1M+"


class TestSuppressLowCounts:
    def test_suppresses_rare(self):
        df = pd.DataFrame(
            {"dept": ["Eng"] * 10 + ["Rare"] * 2 + ["Mkt"] * 8}
        )
        result = suppress_low_counts(df, "dept", threshold=5)
        assert "[SUPPRESSED]" in result["dept"].values
        assert "Eng" in result["dept"].values
