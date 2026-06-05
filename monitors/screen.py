from __future__ import annotations
import logging
import time
import threading
from typing import Callable

import win32gui
import win32process
import psutil

from config import Config
from types_ import ScreenViolation

_log = logging.getLogger(__name__)

try:
    import uiautomation as _auto
    _HAS_UIAUTOMATION = True
except ImportError:
    _auto = None
    _HAS_UIAUTOMATION = False


def get_process_name(hwnd: int) -> str:
    try:
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        return psutil.Process(pid).name().lower()
    except Exception:
        return ""


def get_browser_url(hwnd: int) -> str | None:
    if not _HAS_UIAUTOMATION:
        return None
    try:
        win = _auto.ControlFromHandle(hwnd)
        for name in ("Address and search bar", "urlbar-input"):
            bar = win.EditControl(searchDepth=12, Name=name)
            if bar.Exists(0.1):
                return bar.GetValuePattern().Value
    except Exception:
        pass
    return None


def is_blocked_domain(url: str, config: Config) -> bool:
    if not url:
        return False
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url if "://" in url else f"https://{url}")
        hostname = (parsed.hostname or "").lower()
        return any(
            hostname == domain or hostname.endswith(f".{domain}")
            for domain in config.blocked_domains
        )
    except Exception:
        return any(domain in url for domain in config.blocked_domains)


class ScreenMonitor:
    def __init__(self, config: Config, on_violation: Callable[[ScreenViolation], None]):
        self._config = config
        self._on_violation = on_violation
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

    def start(self) -> None:
        with self._lock:
            if self._thread and self._thread.is_alive():
                return
            self._stop.clear()
            self._thread = threading.Thread(target=self._loop, daemon=True)
            self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        with self._lock:
            thread = self._thread
        if thread:
            thread.join(timeout=5)

    def _loop(self) -> None:
        # uiautomation requires COM initialized on each thread
        if _HAS_UIAUTOMATION:
            try:
                import comtypes
                comtypes.CoInitialize()
            except Exception as e:
                _log.debug("CoInitialize failed: %s", e)
        try:
            while not self._stop.is_set():
                self._check()
                self._stop.wait(timeout=2.0)
        finally:
            if _HAS_UIAUTOMATION:
                try:
                    import comtypes
                    comtypes.CoUninitialize()
                except Exception:
                    pass

    def _check(self) -> None:
        try:
            hwnd = win32gui.GetForegroundWindow()
            title = win32gui.GetWindowText(hwnd)
            process = get_process_name(hwnd)

            # Check native blocked app
            if any(app.lower() in process for app in self._config.blocked_apps):
                self._on_violation(ScreenViolation(
                    url="",  # no URL for native app violations
                    app_name=process,
                    hwnd=hwnd,
                    timestamp=time.time(),
                ))
                return

            # Try to get exact URL for browser windows
            url = get_browser_url(hwnd) or title
            if is_blocked_domain(url, self._config):
                self._on_violation(ScreenViolation(
                    url=url, app_name=process, hwnd=hwnd, timestamp=time.time()
                ))
        except Exception as e:
            _log.debug("_check() error: %s", e)
