"""Tests for history.recent_files module."""

from __future__ import annotations

from pathlib import Path

import pytest

from deskx.history.recent_files import RecentFilesManager


class TestRecentFilesManager:
    def test_add_and_retrieve(self, tmp_path: Path, sample_csv: Path):
        store = tmp_path / "recent.json"
        mgr = RecentFilesManager(storage_path=store)
        mgr.add(sample_csv)
        assert len(mgr.entries) == 1
        assert mgr.entries[0].path == str(sample_csv.resolve())

    def test_most_recent_first(self, tmp_path: Path):
        store = tmp_path / "recent.json"
        mgr = RecentFilesManager(storage_path=store)
        f1 = tmp_path / "a.csv"
        f2 = tmp_path / "b.csv"
        f1.write_text("a")
        f2.write_text("b")
        mgr.add(f1)
        mgr.add(f2)
        assert mgr.entries[0].path == str(f2.resolve())

    def test_duplicate_bumped_to_top(self, tmp_path: Path):
        store = tmp_path / "recent.json"
        mgr = RecentFilesManager(storage_path=store)
        f1 = tmp_path / "a.csv"
        f2 = tmp_path / "b.csv"
        f1.write_text("a")
        f2.write_text("b")
        mgr.add(f1)
        mgr.add(f2)
        mgr.add(f1)  # Bump f1 to top
        assert len(mgr.entries) == 2
        assert mgr.entries[0].path == str(f1.resolve())

    def test_max_entries_enforced(self, tmp_path: Path):
        store = tmp_path / "recent.json"
        mgr = RecentFilesManager(storage_path=store, max_entries=3)
        for i in range(5):
            f = tmp_path / f"file{i}.csv"
            f.write_text(str(i))
            mgr.add(f)
        assert len(mgr.entries) == 3

    def test_remove(self, tmp_path: Path, sample_csv: Path):
        store = tmp_path / "recent.json"
        mgr = RecentFilesManager(storage_path=store)
        mgr.add(sample_csv)
        mgr.remove(sample_csv)
        assert len(mgr.entries) == 0

    def test_clear(self, tmp_path: Path, sample_csv: Path):
        store = tmp_path / "recent.json"
        mgr = RecentFilesManager(storage_path=store)
        mgr.add(sample_csv)
        mgr.clear()
        assert len(mgr.entries) == 0

    def test_persistence(self, tmp_path: Path, sample_csv: Path):
        store = tmp_path / "recent.json"
        mgr1 = RecentFilesManager(storage_path=store)
        mgr1.add(sample_csv)

        # Create a new instance that loads from the same file
        mgr2 = RecentFilesManager(storage_path=store)
        assert len(mgr2.entries) == 1
        assert mgr2.entries[0].path == str(sample_csv.resolve())

    def test_corrupt_store_handled(self, tmp_path: Path):
        store = tmp_path / "recent.json"
        store.write_text("NOT VALID JSON {{{{")
        mgr = RecentFilesManager(storage_path=store)
        assert len(mgr.entries) == 0  # Gracefully reset
