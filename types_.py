from __future__ import annotations
from dataclasses import dataclass


@dataclass
class ScreenViolation:
    url: str
    app_name: str
    hwnd: int
    timestamp: float


@dataclass
class CameraViolation:
    confidence: float
    bbox: tuple[float, float, float, float]  # normalized (x1,y1,x2,y2)
    wrist_dist: float
    timestamp: float


@dataclass
class SessionStats:
    duration_seconds: float
    screen_violations: int
    camera_violations: int
    longest_clean_seconds: float
    streak_days: int

    @property
    def duration_str(self) -> str:
        m, s = divmod(int(self.duration_seconds), 60)
        h, m = divmod(m, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"

    @property
    def longest_clean_str(self) -> str:
        m, s = divmod(int(self.longest_clean_seconds), 60)
        return f"{m:02d}:{s:02d}"
