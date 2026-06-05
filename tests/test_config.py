import json
import os
import tempfile
import pytest
from config import Config, load_config, save_config

def test_defaults():
    c = Config()
    assert c.blocked_domains == ["instagram.com", "tiktok.com", "x.com", "reddit.com", "youtube.com"]
    assert c.grace_seconds == 10
    assert c.nudge_seconds == 30
    assert c.cooldown_seconds == 60
    assert c.exit_grace_seconds == 5
    assert c.camera_enabled is True
    assert c.wrist_phone_threshold == 0.15
    assert c.pomodoro_focus_minutes == 25
    assert c.pomodoro_break_minutes == 5

def test_save_and_load_roundtrip(tmp_path):
    c = Config(grace_seconds=20, blocked_domains=["reddit.com"])
    path = str(tmp_path / "config.json")
    save_config(c, path)
    loaded = load_config(path)
    assert loaded.grace_seconds == 20
    assert loaded.blocked_domains == ["reddit.com"]

def test_load_missing_file_returns_defaults(tmp_path):
    path = str(tmp_path / "nonexistent.json")
    c = load_config(path)
    assert c.grace_seconds == 10

def test_load_partial_json_merges_defaults(tmp_path):
    path = str(tmp_path / "config.json")
    with open(path, "w") as f:
        json.dump({"grace_seconds": 15}, f)
    c = load_config(path)
    assert c.grace_seconds == 15
    assert c.nudge_seconds == 30  # default preserved
