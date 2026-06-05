from __future__ import annotations
import logging
import os
import threading

import pygame

_log = logging.getLogger(__name__)
_mixer_initialized = False


def play_alarm(wav_path: str) -> None:
    global _mixer_initialized
    path = os.path.expanduser(wav_path)
    if not os.path.exists(path):
        _log.warning("play_alarm: file not found: %s", path)
        return
    try:
        if not _mixer_initialized:
            pygame.mixer.init()
            _mixer_initialized = True
        pygame.mixer.music.load(path)
        pygame.mixer.music.play()
    except Exception as e:
        _log.warning("play_alarm error: %s", e)


def play_video(video_path: str) -> None:
    path = os.path.expanduser(video_path)
    if not os.path.exists(path):
        _log.info("play_video: file not found (no motivation.mp4 configured): %s", path)
        return
    try:
        os.startfile(path)
    except Exception as e:
        _log.warning("play_video error: %s", e)
