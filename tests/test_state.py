"""Tests for the persistent state store."""

from __future__ import annotations

import json
from pathlib import Path

from s365watch.state import StateStore


def test_load_missing_file_starts_empty(tmp_path: Path) -> None:
    store = StateStore(tmp_path / "seen.json")
    store.load()
    assert store.is_empty
    assert store.diff({1, 2}) == {1, 2}


def test_diff_returns_only_unseen_ids(tmp_path: Path) -> None:
    store = StateStore(tmp_path / "seen.json")
    store.mark_seen({1, 2, 3})
    assert store.diff({2, 3, 4, 5}) == {4, 5}


def test_save_then_load_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "nested" / "seen.json"
    store = StateStore(path)
    store.mark_seen({10, 20, 30})
    store.save()

    reloaded = StateStore(path)
    reloaded.load()
    assert not reloaded.is_empty
    assert reloaded.diff({10, 20, 30, 40}) == {40}


def test_save_writes_sorted_json(tmp_path: Path) -> None:
    path = tmp_path / "seen.json"
    store = StateStore(path)
    store.mark_seen({3, 1, 2})
    store.save()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data == {"seen_ids": [1, 2, 3]}


def test_save_leaves_no_temp_files(tmp_path: Path) -> None:
    store = StateStore(tmp_path / "seen.json")
    store.mark_seen({1})
    store.save()
    assert [p.name for p in tmp_path.iterdir()] == ["seen.json"]
