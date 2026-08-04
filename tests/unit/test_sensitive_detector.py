"""Tests for processing.sensitive_detector module."""

from __future__ import annotations

import pandas as pd
import pytest

from deskx.processing.sensitive_detector import (
    SensitiveColumn,
    detect_sensitive_columns,
)


@pytest.fixture
def pii_df():
    """DataFrame with PII-like data."""
    return pd.DataFrame({
        "employee_id": [1, 2, 3, 4, 5],
        "first_name": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
        "email": [
            "alice@example.com", "bob@example.com", "charlie@example.com",
            "diana@example.com", "eve@example.com",
        ],
        "phone": [
            "(555) 123-4567", "(555) 234-5678", "(555) 345-6789",
            "(555) 456-7890", "(555) 567-8901",
        ],
        "salary": [75000, 62000, 85000, 55000, 92000],
        "department": ["Eng", "Mkt", "Eng", "HR", "Sales"],
    })


@pytest.fixture
def clean_df():
    """DataFrame without PII."""
    return pd.DataFrame({
        "product_id": [1, 2, 3],
        "category": ["Electronics", "Books", "Clothing"],
        "quantity": [100, 250, 75],
    })


class TestDetectSensitiveColumns:
    def test_detects_email_column(self, pii_df):
        results = detect_sensitive_columns(pii_df)
        email_results = [r for r in results if r.column_name == "email"]
        assert len(email_results) > 0
        assert email_results[0].category in ("email",)
        assert email_results[0].confidence > 0.5

    def test_detects_name_column(self, pii_df):
        results = detect_sensitive_columns(pii_df)
        name_results = [r for r in results if r.column_name == "first_name"]
        assert len(name_results) > 0
        assert name_results[0].category == "name"

    def test_detects_financial_column(self, pii_df):
        results = detect_sensitive_columns(pii_df)
        salary_results = [r for r in results if r.column_name == "salary"]
        assert len(salary_results) > 0
        assert salary_results[0].category == "financial"

    def test_clean_data_returns_fewer(self, clean_df):
        results = detect_sensitive_columns(clean_df)
        # clean_df has no obvious PII columns
        # May still flag some based on broad patterns, but fewer
        assert len(results) <= 1

    def test_ordered_by_confidence(self, pii_df):
        results = detect_sensitive_columns(pii_df)
        if len(results) > 1:
            for i in range(len(results) - 1):
                assert results[i].confidence >= results[i + 1].confidence

    def test_suggested_actions(self, pii_df):
        results = detect_sensitive_columns(pii_df)
        for r in results:
            assert r.suggested_action in (
                "mask", "redact", "hash", "pseudonymize", "generalize", "ignore"
            )

    def test_empty_dataframe(self):
        df = pd.DataFrame()
        results = detect_sensitive_columns(df)
        assert results == []

    def test_min_confidence_filter(self, pii_df):
        high_conf = detect_sensitive_columns(pii_df, min_confidence=0.8)
        low_conf = detect_sensitive_columns(pii_df, min_confidence=0.3)
        assert len(high_conf) <= len(low_conf)
