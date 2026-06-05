from __future__ import annotations
import glob
import json
import os
import flet as ft

LOG_PATH = os.path.expanduser("~/.doomscroll/log.jsonl")
SHAME_DIR = os.path.expanduser("~/.doomscroll/shame_shots")


def _load_entries() -> list[dict]:
    if not os.path.exists(LOG_PATH):
        return []
    entries = []
    with open(LOG_PATH) as f:
        for line in f:
            try:
                entries.append(json.loads(line.strip()))
            except Exception:
                pass
    return list(reversed(entries))


def build_log_view() -> ft.Control:
    entries = _load_entries()

    rows = []
    for e in entries[:50]:
        date_str = str(e.get("date", ""))[:16].replace("T", " ")
        dur = int(e.get("duration_seconds", 0))
        m, s = divmod(dur, 60)
        h, m = divmod(m, 60)
        dur_str = f"{h:02d}:{m:02d}:{s:02d}"
        rows.append(ft.DataRow(cells=[
            ft.DataCell(ft.Text(date_str, size=11)),
            ft.DataCell(ft.Text(dur_str, size=11)),
            ft.DataCell(ft.Text(str(e.get("screen_violations", 0)), size=11)),
            ft.DataCell(ft.Text(str(e.get("camera_violations", 0)), size=11)),
        ]))

    table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Date", size=11)),
            ft.DataColumn(ft.Text("Duration", size=11)),
            ft.DataColumn(ft.Text("Screen", size=11), numeric=True),
            ft.DataColumn(ft.Text("Camera", size=11), numeric=True),
        ],
        rows=rows,
        column_spacing=16,
    )

    shots = sorted(glob.glob(os.path.join(SHAME_DIR, "*.jpg")), reverse=True)[:12]
    gallery = ft.Row(
        controls=[
            ft.Image(src=p, width=90, height=68, fit=ft.ImageFit.COVER, border_radius=4)
            for p in shots
        ],
        wrap=True,
        spacing=4,
    )

    return ft.Column(
        [
            ft.Text("Session History", size=15, weight=ft.FontWeight.BOLD),
            ft.Container(
                content=ft.ListView(controls=[table], expand=True),
                height=250,
                border=ft.border.all(1, ft.colors.GREY_700),
                border_radius=4,
            ),
            ft.Divider(),
            ft.Text("Shame Shots", size=13, weight=ft.FontWeight.BOLD),
            gallery if shots else ft.Text("No shame shots yet.", color=ft.colors.GREY_400, size=12),
        ],
        spacing=10,
        width=500,
    )
