from __future__ import annotations
import logging
import threading

import win32gui
import win32con

from config import Config
from interventions.shame import show_shame
from interventions.video import play_alarm, play_video

_log = logging.getLogger(__name__)


def close_window(hwnd: int) -> None:
    if not hwnd:
        return
    try:
        win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
    except Exception as e:
        _log.warning("close_window(%d) error: %s", hwnd, e)


def fire_aggro(config: Config, hwnd: int | None = None) -> None:
    play_alarm(config.alarm_wav_path)
    threading.Thread(target=show_shame, daemon=True).start()
    threading.Thread(target=play_video, args=(config.motivational_video_path,), daemon=True).start()
    if hwnd:
        close_window(hwnd)
