from __future__ import annotations
import logging
import time
import threading
from enum import Enum
from typing import Callable

from config import Config

_log = logging.getLogger(__name__)


class EngineState(Enum):
    CLEAN = "clean"
    GRACE = "grace"
    NUDGED = "nudged"
    AGGRO = "aggro"
    COOLDOWN = "cooldown"


class InterventionEngine:
    def __init__(
        self,
        config: Config,
        on_nudge: Callable[[], None],
        on_aggro: Callable[[], None],
    ):
        self._config = config
        self._on_nudge = on_nudge
        self._on_aggro = on_aggro
        self.state = EngineState.CLEAN
        self._state_entered_at: float = 0.0
        self._last_violation_at: float | None = None
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def report_violation(self) -> None:
        with self._lock:
            now = time.time()
            self._last_violation_at = now
            if self.state == EngineState.CLEAN:
                self.state = EngineState.GRACE
                self._state_entered_at = now

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
        while not self._stop.is_set():
            self._tick()
            self._stop.wait(0.5)

    def _tick(self) -> None:
        with self._lock:
            now = time.time()
            has_violation = (
                self._last_violation_at is not None
                and now - self._last_violation_at < self._config.exit_grace_seconds
            )

            if self.state == EngineState.GRACE:
                if not has_violation:
                    if self._last_violation_at and now - self._last_violation_at >= self._config.exit_grace_seconds:
                        self.state = EngineState.CLEAN
                elif now - self._state_entered_at >= self._config.grace_seconds:
                    self.state = EngineState.NUDGED
                    self._state_entered_at = now
                    threading.Thread(target=self._on_nudge, daemon=True).start()

            elif self.state == EngineState.NUDGED:
                if not has_violation:
                    if self._last_violation_at and now - self._last_violation_at >= self._config.exit_grace_seconds:
                        self.state = EngineState.CLEAN
                elif now - self._state_entered_at >= self._config.nudge_seconds:
                    self.state = EngineState.AGGRO
                    self._state_entered_at = now
                    threading.Thread(target=self._on_aggro, daemon=True).start()

            elif self.state == EngineState.AGGRO:
                self.state = EngineState.COOLDOWN
                self._state_entered_at = now

            elif self.state == EngineState.COOLDOWN:
                if now - self._state_entered_at >= self._config.cooldown_seconds:
                    # If a new violation arrived during cooldown, go to GRACE not CLEAN
                    if (self._last_violation_at is not None and
                            now - self._last_violation_at < self._config.exit_grace_seconds):
                        self.state = EngineState.GRACE
                        self._state_entered_at = now
                    else:
                        self.state = EngineState.CLEAN
                        self._state_entered_at = 0.0
                        self._last_violation_at = None
