"""
Unit tests for extract/checkpoint.py.

Each test points CHECKPOINT_PATH at a throwaway file inside pytest's
tmp_path fixture, so tests never touch the real data/checkpoint.json
and can run in any order without interfering with each other.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "extract"))

import checkpoint  # noqa: E402


def test_read_checkpoint_returns_default_when_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(checkpoint, "CHECKPOINT_PATH", str(tmp_path / "checkpoint.json"))

    assert checkpoint.read_checkpoint() == checkpoint.DEFAULT_START


def test_write_then_read_round_trips(tmp_path, monkeypatch):
    path = str(tmp_path / "checkpoint.json")
    monkeypatch.setattr(checkpoint, "CHECKPOINT_PATH", path)

    checkpoint.write_checkpoint("2025-06-01T00:00:00Z")

    assert checkpoint.read_checkpoint() == "2025-06-01T00:00:00Z"


def test_write_checkpoint_creates_missing_parent_directory(tmp_path, monkeypatch):
    nested_path = str(tmp_path / "nested" / "dir" / "checkpoint.json")
    monkeypatch.setattr(checkpoint, "CHECKPOINT_PATH", nested_path)

    checkpoint.write_checkpoint("2025-06-01T00:00:00Z")

    assert os.path.exists(nested_path)


def test_write_checkpoint_records_updated_at(tmp_path, monkeypatch):
    path = str(tmp_path / "checkpoint.json")
    monkeypatch.setattr(checkpoint, "CHECKPOINT_PATH", path)

    checkpoint.write_checkpoint("2025-06-01T00:00:00Z")

    with open(path) as f:
        data = json.load(f)

    assert data["last_successful_run_through"] == "2025-06-01T00:00:00Z"
    assert "updated_at" in data


def test_new_checkpoint_overwrites_previous_value(tmp_path, monkeypatch):
    path = str(tmp_path / "checkpoint.json")
    monkeypatch.setattr(checkpoint, "CHECKPOINT_PATH", path)

    checkpoint.write_checkpoint("2025-06-01T00:00:00Z")
    checkpoint.write_checkpoint("2025-07-01T00:00:00Z")

    assert checkpoint.read_checkpoint() == "2025-07-01T00:00:00Z"
