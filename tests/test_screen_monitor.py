import time
import pytest
from unittest.mock import patch, MagicMock
from monitors.screen import ScreenMonitor, is_blocked_domain, get_browser_url
from config import Config
from types_ import ScreenViolation


def test_is_blocked_domain_matches():
    config = Config(blocked_domains=["instagram.com", "reddit.com"])
    assert is_blocked_domain("https://www.instagram.com/feed", config) is True
    assert is_blocked_domain("https://reddit.com/r/python", config) is True

def test_is_blocked_domain_no_match():
    config = Config(blocked_domains=["instagram.com"])
    assert is_blocked_domain("https://github.com", config) is False
    # IMPORTANT: x.com should NOT match example.com
    config2 = Config(blocked_domains=["x.com"])
    assert is_blocked_domain("https://example.com", config2) is False

def test_is_blocked_domain_subdomain():
    config = Config(blocked_domains=["reddit.com"])
    assert is_blocked_domain("https://old.reddit.com/r/python", config) is True

def test_is_blocked_domain_empty_url():
    assert is_blocked_domain("", Config()) is False

def test_monitor_emits_violation_for_blocked_url(mocker):
    config = Config()
    violations = []
    monitor = ScreenMonitor(config, on_violation=violations.append)

    mocker.patch("monitors.screen.win32gui.GetForegroundWindow", return_value=99)
    mocker.patch("monitors.screen.win32gui.GetWindowText", return_value="Instagram - Google Chrome")
    mocker.patch("monitors.screen.get_browser_url", return_value="https://www.instagram.com/")
    mocker.patch("monitors.screen.get_process_name", return_value="chrome.exe")

    monitor._check()

    assert len(violations) == 1
    assert "instagram.com" in violations[0].url

def test_monitor_no_violation_for_allowed_url(mocker):
    config = Config()
    violations = []
    monitor = ScreenMonitor(config, on_violation=violations.append)

    mocker.patch("monitors.screen.win32gui.GetForegroundWindow", return_value=99)
    mocker.patch("monitors.screen.win32gui.GetWindowText", return_value="GitHub - Google Chrome")
    mocker.patch("monitors.screen.get_browser_url", return_value="https://github.com/")
    mocker.patch("monitors.screen.get_process_name", return_value="chrome.exe")

    monitor._check()
    assert len(violations) == 0

def test_monitor_detects_native_blocked_app(mocker):
    config = Config(blocked_apps=["tiktok.exe"])
    violations = []
    monitor = ScreenMonitor(config, on_violation=violations.append)

    mocker.patch("monitors.screen.win32gui.GetForegroundWindow", return_value=99)
    mocker.patch("monitors.screen.win32gui.GetWindowText", return_value="TikTok")
    mocker.patch("monitors.screen.get_browser_url", return_value=None)
    mocker.patch("monitors.screen.get_process_name", return_value="tiktok.exe")

    monitor._check()
    assert len(violations) == 1
