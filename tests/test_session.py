import json
import os
import time
import pytest
from unittest.mock import MagicMock, patch
from session import Session, SessionState, load_streak, save_streak
from config import Config
from types_ import SessionStats


def test_initial_state_is_idle():
    s = Session(Config(), MagicMock(), MagicMock(), MagicMock())
    assert s.state == SessionState.IDLE


def test_start_sets_active():
    s = Session(Config(), MagicMock(), MagicMock(), MagicMock())
    s.start()
    assert s.state == SessionState.ACTIVE
    s.stop()


def test_stop_returns_stats():
    s = Session(Config(), MagicMock(), MagicMock(), MagicMock())
    s.start()
    time.sleep(0.05)
    stats = s.stop()
    assert isinstance(stats, SessionStats)
    assert stats.duration_seconds >= 0


def test_violation_counts_increment():
    s = Session(Config(), MagicMock(), MagicMock(), MagicMock())
    s.start()
    from types_ import ScreenViolation, CameraViolation
    s._on_screen_violation(ScreenViolation("instagram.com", "chrome.exe", 0, time.time()))
    s._on_screen_violation(ScreenViolation("reddit.com", "chrome.exe", 0, time.time()))
    s._on_camera_violation(CameraViolation(0.9, (0,0,0,0), 0.1, time.time()))
    stats = s.stop()
    assert stats.screen_violations == 2
    assert stats.camera_violations == 1


def test_streak_load_missing_returns_zero(tmp_path):
    streak = load_streak(str(tmp_path / "streak.json"))
    assert streak == 0


def test_streak_save_and_load(tmp_path):
    path = str(tmp_path / "streak.json")
    save_streak(5, path)
    assert load_streak(path) == 5
