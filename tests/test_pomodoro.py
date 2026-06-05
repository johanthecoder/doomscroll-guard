import time
import pytest
from unittest.mock import MagicMock
from session import PomodoroTimer, PomodoroPhase


def test_starts_in_focus():
    on_break = MagicMock()
    on_focus = MagicMock()
    t = PomodoroTimer(focus_minutes=0.01, break_minutes=0.01, on_break=on_break, on_focus=on_focus)
    assert t.phase == PomodoroPhase.FOCUS


def test_transitions_focus_to_break():
    on_break = MagicMock()
    on_focus = MagicMock()
    t = PomodoroTimer(focus_minutes=0.01, break_minutes=0.01, on_break=on_break, on_focus=on_focus)
    t.start()
    time.sleep(1.5)
    on_break.assert_called()
    t.stop()


def test_transitions_break_to_focus():
    on_break = MagicMock()
    on_focus = MagicMock()
    t = PomodoroTimer(focus_minutes=0.01, break_minutes=0.01, on_break=on_break, on_focus=on_focus)
    t.start()
    time.sleep(2.5)
    on_focus.assert_called()
    t.stop()
