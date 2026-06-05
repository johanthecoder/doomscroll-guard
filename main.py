from __future__ import annotations
import logging
import os

import flet as ft

from config import Config, load_config
from monitors.screen import ScreenMonitor
from monitors.camera import CameraMonitor
from interventions.engine import InterventionEngine
from interventions.nudge import send_nudge
from interventions.aggro import fire_aggro
from session import Session
from ui.app import build_app

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)

CONFIG_PATH = os.path.expanduser("~/.doomscroll/config.json")


def main() -> None:
    config = load_config(CONFIG_PATH)

    # Placeholder callbacks — real callbacks wired after session created
    screen_monitor = ScreenMonitor(config, on_violation=lambda v: None)
    camera_monitor = CameraMonitor(config, on_violation=lambda v: None)

    last_screen_hwnd: list[int] = [0]

    def on_nudge() -> None:
        send_nudge()

    def on_aggro() -> None:
        fire_aggro(config, hwnd=last_screen_hwnd[0])

    engine = InterventionEngine(config, on_nudge=on_nudge, on_aggro=on_aggro)
    session = Session(config, screen_monitor, camera_monitor, engine)

    # Wrap screen violation to track last hwnd for aggro window closing
    _orig_screen_violation = session._on_screen_violation

    def _screen_violation_with_hwnd(v):
        last_screen_hwnd[0] = v.hwnd
        _orig_screen_violation(v)

    screen_monitor._on_violation = _screen_violation_with_hwnd

    app_main = build_app(session, config)
    ft.app(target=app_main)


if __name__ == "__main__":
    main()
