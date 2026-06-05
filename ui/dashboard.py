from __future__ import annotations
import logging
import time
import threading
import numpy as np
import flet as ft

from ui.helpers import frame_to_b64, seconds_to_hms
from session import SessionState, load_streak
from config import Config

_log = logging.getLogger(__name__)


def build_dashboard(page: ft.Page, session, config: Config) -> ft.Control:
    blank = np.zeros((240, 320, 3), dtype=np.uint8)
    camera_img = ft.Image(
        src_base64=frame_to_b64(blank),
        width=320,
        height=240,
        fit=ft.ImageFit.CONTAIN,
        border_radius=8,
    )

    camera_status = ft.Text("Camera initializing (~10s)...", size=11, color=ft.colors.GREY_500)
    status_text = ft.Text("IDLE", size=12, color=ft.colors.GREY_400)
    timer_text = ft.Text("00:00:00", size=32, weight=ft.FontWeight.BOLD)
    streak_text = ft.Text("", size=13, color=ft.colors.ORANGE_300)
    screen_count = ft.Text("Screen:  0", size=13)
    camera_count = ft.Text("Camera:  0", size=13)

    start_btn = ft.ElevatedButton(
        "START",
        bgcolor=ft.colors.GREEN_700,
        color=ft.colors.WHITE,
        width=140,
    )
    pause_btn = ft.ElevatedButton(
        "PAUSE",
        bgcolor=ft.colors.AMBER_700,
        color=ft.colors.WHITE,
        width=140,
        disabled=True,
    )

    def _refresh_counts():
        screen_count.value = f"Screen:  {session._screen_violations}"
        camera_count.value = f"Camera:  {session._camera_violations}"

    def _on_start(e):
        session.start()
        start_btn.text = "STOP"
        start_btn.bgcolor = ft.colors.RED_700
        pause_btn.disabled = False
        status_text.value = "MONITORING"
        status_text.color = ft.colors.GREEN_400
        page.update()

    def _on_stop(e):
        stats = session.stop()
        start_btn.text = "START"
        start_btn.bgcolor = ft.colors.GREEN_700
        pause_btn.disabled = True
        pause_btn.text = "PAUSE"
        status_text.value = "IDLE"
        status_text.color = ft.colors.GREY_400
        timer_text.value = "00:00:00"
        screen_count.value = "Screen:  0"
        camera_count.value = "Camera:  0"
        page.update()
        from ui.summary import show_summary
        show_summary(page, stats)

    def _toggle_session(e):
        if session.state == SessionState.ACTIVE:
            _on_stop(e)
        else:
            _on_start(e)

    start_btn.on_click = _toggle_session

    def _toggle_pause(e):
        if session.state == SessionState.ACTIVE:
            session.pause()
            pause_btn.text = "RESUME"
            status_text.value = "PAUSED"
        else:
            session.resume()
            pause_btn.text = "PAUSE"
            status_text.value = "MONITORING"
        page.update()

    pause_btn.on_click = _toggle_pause

    def _update_loop():
        _last_stats_at = 0.0
        while True:
            time.sleep(0.2)
            if session.state != SessionState.ACTIVE:
                continue
            try:
                now = time.time()

                # Camera feed — every 200ms, update only that control
                frame = session._camera_monitor.latest_frame
                if frame is not None:
                    if camera_status.visible:
                        camera_status.visible = False
                        camera_status.update()
                    camera_img.src_base64 = frame_to_b64(frame)
                    camera_img.update()

                # Stats — every 1s to avoid hammering the event queue
                if now - _last_stats_at >= 1.0:
                    _last_stats_at = now
                    timer_text.value = seconds_to_hms(now - session._start_time)
                    timer_text.update()
                    new_screen = f"Screen:  {session._screen_violations}"
                    new_camera = f"Camera:  {session._camera_violations}"
                    if screen_count.value != new_screen:
                        screen_count.value = new_screen
                        screen_count.update()
                    if camera_count.value != new_camera:
                        camera_count.value = new_camera
                        camera_count.update()
            except Exception as e:
                _log.warning("_update_loop error: %s", e)
                continue

    threading.Thread(target=_update_loop, daemon=True).start()

    left_col = ft.Column(
        [camera_img, camera_status, status_text],
        spacing=4,
    )

    right_col = ft.Column(
        [
            ft.Text("SESSION", size=11, color=ft.colors.GREY_400),
            timer_text,
            streak_text,
            ft.Divider(height=1, color=ft.colors.GREY_700),
            ft.Text("Violations today", size=11, color=ft.colors.GREY_400),
            screen_count,
            camera_count,
            ft.Container(height=8),
            start_btn,
            pause_btn,
        ],
        spacing=6,
        width=200,
    )

    bottom_bar = ft.Row(
        [
            ft.TextButton("⚙ Settings", on_click=lambda e: _open_settings(page, config)),
            ft.TextButton("🍅 Pomodoro", on_click=lambda e: None),
            ft.TextButton("📋 Log", on_click=lambda e: _open_log(page)),
        ],
        alignment=ft.MainAxisAlignment.SPACE_AROUND,
    )

    return ft.Column(
        [
            ft.Container(
                content=ft.Row([left_col, ft.Container(width=16), right_col]),
                padding=ft.padding.all(16),
            ),
            ft.Divider(height=1, color=ft.colors.GREY_700),
            bottom_bar,
        ],
        spacing=0,
        expand=True,
    )


def _open_settings(page: ft.Page, config: Config):
    from ui.settings import build_settings_sheet
    page.open(build_settings_sheet(page, config))


def _open_log(page: ft.Page):
    from ui.log import build_log_view
    dlg = ft.AlertDialog(
        title=ft.Text("Session Log"),
        content=build_log_view(),
        actions=[ft.TextButton("Close", on_click=lambda e: page.close(dlg))],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    page.open(dlg)
