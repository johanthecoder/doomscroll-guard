from __future__ import annotations
import flet as ft
from types_ import SessionStats


def show_summary(page: ft.Page, stats: SessionStats) -> None:
    def _close(e):
        page.close(dlg)

    dlg = ft.AlertDialog(
        modal=True,
        title=ft.Text("Session Complete", size=20, weight=ft.FontWeight.BOLD),
        content=ft.Column(
            [
                ft.ListTile(
                    leading=ft.Icon(ft.icons.TIMER),
                    title=ft.Text("Duration"),
                    trailing=ft.Text(stats.duration_str, weight=ft.FontWeight.BOLD),
                ),
                ft.ListTile(
                    leading=ft.Icon(ft.icons.MONITOR, color=ft.colors.RED_400),
                    title=ft.Text("Screen catches"),
                    trailing=ft.Text(str(stats.screen_violations), weight=ft.FontWeight.BOLD),
                ),
                ft.ListTile(
                    leading=ft.Icon(ft.icons.VIDEOCAM, color=ft.colors.RED_400),
                    title=ft.Text("Camera catches"),
                    trailing=ft.Text(str(stats.camera_violations), weight=ft.FontWeight.BOLD),
                ),
                ft.ListTile(
                    leading=ft.Icon(ft.icons.SELF_IMPROVEMENT, color=ft.colors.GREEN_400),
                    title=ft.Text("Longest clean"),
                    trailing=ft.Text(stats.longest_clean_str, weight=ft.FontWeight.BOLD),
                ),
                ft.Container(
                    content=ft.Text(
                        f"🔥 {stats.streak_days} day streak",
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        color=ft.colors.ORANGE_300,
                    ),
                    alignment=ft.alignment.center,
                    padding=ft.padding.symmetric(vertical=8),
                ),
            ],
            tight=True,
            width=340,
        ),
        actions=[ft.TextButton("Close", on_click=_close)],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    page.open(dlg)
