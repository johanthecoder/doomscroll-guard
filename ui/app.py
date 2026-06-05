from __future__ import annotations
import flet as ft


def build_app(session, config):
    def main(page: ft.Page):
        page.title = "Doomscroll Guard"
        page.theme_mode = ft.ThemeMode.DARK
        page.window.width = 720
        page.window.height = 520
        page.window.resizable = False
        page.bgcolor = ft.colors.SURFACE_VARIANT

        from ui.dashboard import build_dashboard
        dashboard = build_dashboard(page, session, config)
        page.add(dashboard)
        page.update()

    return main
