from __future__ import annotations
import os
import flet as ft
from config import Config, save_config

CONFIG_PATH = os.path.expanduser("~/.doomscroll/config.json")


def build_settings_sheet(page: ft.Page, config: Config) -> ft.BottomSheet:
    chips_row = ft.Row(wrap=True, controls=[
        _make_chip(d, config, page) for d in config.blocked_domains
    ])

    new_domain_field = ft.TextField(
        label="Add domain",
        hint_text="e.g. twitch.tv",
        width=180,
        height=45,
    )

    def _add_domain(e):
        d = (new_domain_field.value or "").strip().lower()
        if d and d not in config.blocked_domains:
            config.blocked_domains.append(d)
            chips_row.controls.append(_make_chip(d, config, page))
            new_domain_field.value = ""
            page.update()

    grace_slider = ft.Slider(
        min=5, max=30, value=config.grace_seconds, divisions=25,
        label="{value}s",
        on_change=lambda e: setattr(config, "grace_seconds", int(e.control.value)),
    )
    nudge_slider = ft.Slider(
        min=15, max=60, value=config.nudge_seconds, divisions=45,
        label="{value}s",
        on_change=lambda e: setattr(config, "nudge_seconds", int(e.control.value)),
    )
    camera_toggle = ft.Switch(
        label="Camera detection",
        value=config.camera_enabled,
        on_change=lambda e: setattr(config, "camera_enabled", e.control.value),
    )
    video_field = ft.TextField(
        label="Motivational video path",
        value=config.motivational_video_path,
        expand=True,
        on_change=lambda e: setattr(config, "motivational_video_path", e.control.value),
    )

    def _save(e):
        save_config(config, CONFIG_PATH)
        page.close(sheet)
        sb = ft.SnackBar(ft.Text("Settings saved ✓"))
        page.overlay.append(sb)
        sb.open = True
        page.update()

    sheet = ft.BottomSheet(
        content=ft.Container(
            content=ft.Column(
                [
                    ft.Text("Settings", size=18, weight=ft.FontWeight.BOLD),
                    ft.Text("Blocked domains", size=12, color=ft.colors.GREY_400),
                    chips_row,
                    ft.Row([new_domain_field, ft.IconButton(ft.icons.ADD, on_click=_add_domain)]),
                    ft.Text("Grace period", size=12, color=ft.colors.GREY_400),
                    grace_slider,
                    ft.Text("Escalation timer", size=12, color=ft.colors.GREY_400),
                    nudge_slider,
                    camera_toggle,
                    video_field,
                    ft.ElevatedButton(
                        "Save", on_click=_save,
                        bgcolor=ft.colors.GREEN_700, color=ft.colors.WHITE,
                    ),
                ],
                scroll=ft.ScrollMode.AUTO,
                spacing=10,
            ),
            padding=20,
            height=480,
        ),
    )
    return sheet


def _make_chip(domain: str, config: Config, page: ft.Page) -> ft.Chip:
    def _remove(e):
        if domain in config.blocked_domains:
            config.blocked_domains.remove(domain)
        page.update()

    return ft.Chip(label=ft.Text(domain, size=12), on_delete=_remove)
