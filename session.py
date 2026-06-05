from __future__ import annotations
import json
import logging
import os
import threading
import time
from datetime import datetime, date
from enum import Enum
from typing import Callable

from config import Config
from monitors.screen import ScreenMonitor
from monitors.camera import CameraMonitor
from interventions.engine import InterventionEngine
from types_ import ScreenViolation, CameraViolation, SessionStats

_log = logging.getLogger(__name__)

DEFAULT_LOG_PATH = os.path.expanduser("~/.doomscroll/log.jsonl")
DEFAULT_STREAK_PATH = os.path.expanduser("~/.doomscroll/streak.json")


def load_streak(path: str = DEFAULT_STREAK_PATH) -> int:
    try:
        with open(path) as f:
            data = json.load(f)
        return int(data.get("streak", 0))
    except (FileNotFoundError, json.JSONDecodeError, ValueError, KeyError):
        return 0


def save_streak(streak: int, path: str = DEFAULT_STREAK_PATH) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w") as f:
        json.dump({"streak": streak, "last_updated": str(date.today())}, f)


class SessionState(Enum):
    IDLE = "idle"
    ACTIVE = "active"
    PAUSED = "paused"
    BREAK = "break"


class Session:
    def __init__(
        self,
        config: Config,
        screen_monitor: ScreenMonitor,
        camera_monitor: CameraMonitor,
        engine: InterventionEngine,
        log_path: str = DEFAULT_LOG_PATH,
        streak_path: str = DEFAULT_STREAK_PATH,
    ):
        self._config = config
        self._screen_monitor = screen_monitor
        self._camera_monitor = camera_monitor
        self._engine = engine
        self._log_path = log_path
        self._streak_path = streak_path

        self.state = SessionState.IDLE
        self._start_time: float = 0.0
        self._screen_violations: int = 0
        self._camera_violations: int = 0
        self._clean_start: float = 0.0
        self._longest_clean: float = 0.0
        self._last_violation_time: float = 0.0
        self._lock = threading.Lock()

    def start(self) -> None:
        with self._lock:
            self._start_time = time.time()
            self._clean_start = self._start_time
            self._screen_violations = 0
            self._camera_violations = 0
            self._longest_clean = 0.0
            self._last_violation_time = 0.0
            self.state = SessionState.ACTIVE

        # Wire monitor callbacks
        self._screen_monitor._on_violation = self._on_screen_violation
        self._camera_monitor._on_violation = self._on_camera_violation

        self._screen_monitor.start()
        if self._config.camera_enabled:
            self._camera_monitor.start()
        self._engine.start()

    def stop(self) -> SessionStats:
        self._screen_monitor.stop()
        self._camera_monitor.stop()
        self._engine.stop()

        with self._lock:
            now = time.time()
            self.state = SessionState.IDLE
            duration = now - self._start_time
            self._update_longest_clean(now)
            current_streak = load_streak(self._streak_path)
            clean = self._screen_violations == 0 and self._camera_violations == 0
            new_streak = current_streak + 1 if clean else 0
            save_streak(new_streak, self._streak_path)
            stats = SessionStats(
                duration_seconds=duration,
                screen_violations=self._screen_violations,
                camera_violations=self._camera_violations,
                longest_clean_seconds=self._longest_clean,
                streak_days=new_streak,
            )

        self._write_log(stats)
        return stats

    def pause(self) -> None:
        self.state = SessionState.PAUSED
        self._engine.stop()

    def resume(self) -> None:
        self.state = SessionState.ACTIVE
        self._engine.start()

    def _on_screen_violation(self, v: ScreenViolation) -> None:
        with self._lock:
            self._screen_violations += 1
            self._update_longest_clean(v.timestamp)
            self._last_violation_time = v.timestamp
        self._engine.report_violation()

    def _on_camera_violation(self, v: CameraViolation) -> None:
        with self._lock:
            self._camera_violations += 1
            self._update_longest_clean(v.timestamp)
            self._last_violation_time = v.timestamp
        self._engine.report_violation()

    def _update_longest_clean(self, now: float) -> None:
        if self._last_violation_time > 0:
            clean_duration = now - self._last_violation_time
        else:
            clean_duration = now - self._clean_start
        if clean_duration > self._longest_clean:
            self._longest_clean = clean_duration

    def _write_log(self, stats: SessionStats) -> None:
        try:
            os.makedirs(os.path.dirname(os.path.abspath(self._log_path)), exist_ok=True)
            entry = {
                "date": datetime.now().isoformat(),
                "duration_seconds": stats.duration_seconds,
                "screen_violations": stats.screen_violations,
                "camera_violations": stats.camera_violations,
                "longest_clean_seconds": stats.longest_clean_seconds,
            }
            with open(self._log_path, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            _log.warning("Failed to write session log: %s", e)


class PomodoroPhase(Enum):
    FOCUS = "focus"
    BREAK = "break"


class PomodoroTimer:
    def __init__(
        self,
        focus_minutes: float,
        break_minutes: float,
        on_break: Callable[[], None],
        on_focus: Callable[[], None],
    ):
        self.phase = PomodoroPhase.FOCUS
        self._focus_secs = focus_minutes * 60
        self._break_secs = break_minutes * 60
        self._on_break = on_break
        self._on_focus = on_focus
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5)

    def _loop(self) -> None:
        while not self._stop.is_set():
            self._stop.wait(self._focus_secs)
            if self._stop.is_set():
                break
            self.phase = PomodoroPhase.BREAK
            self._on_break()
            self._stop.wait(self._break_secs)
            if self._stop.is_set():
                break
            self.phase = PomodoroPhase.FOCUS
            self._on_focus()
