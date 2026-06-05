from __future__ import annotations
import json
import os
from dataclasses import dataclass, field, asdict


@dataclass
class Config:
    blocked_domains: list[str] = field(
        default_factory=lambda: ["instagram.com", "tiktok.com", "x.com", "reddit.com", "youtube.com"]
    )
    blocked_apps: list[str] = field(default_factory=list)
    grace_seconds: int = 10
    exit_grace_seconds: int = 5
    nudge_seconds: int = 30
    cooldown_seconds: int = 60
    camera_enabled: bool = True
    wrist_phone_threshold: float = 0.15
    camera_phone_area_max: float = 0.20
    motivational_video_path: str = "assets/motivation.mp4"
    alarm_wav_path: str = "assets/alarm.wav"
    pomodoro_focus_minutes: int = 25
    pomodoro_break_minutes: int = 5


def load_config(path: str) -> Config:
    defaults = asdict(Config())
    if not os.path.exists(path):
        return Config()
    try:
        with open(path) as f:
            data = json.load(f)
        defaults.update(data)
        # Replace None values with field defaults (handles null in JSON)
        fallback = asdict(Config())
        defaults = {k: (v if v is not None else fallback[k]) for k, v in defaults.items()}
        return Config(**{k: v for k, v in defaults.items() if k in Config.__dataclass_fields__})
    except (json.JSONDecodeError, IOError, OSError, TypeError, ValueError):
        return Config()


def save_config(config: Config, path: str) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        json.dump(asdict(config), f, indent=2)
