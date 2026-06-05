import numpy as np
import pytest
from unittest.mock import MagicMock, patch
from monitors.camera import is_phone_held, annotate_frame
from config import Config


def test_phone_held_when_wrist_near_phone():
    config = Config(wrist_phone_threshold=0.15)
    phone = np.array([0.3, 0.3, 0.5, 0.6])  # center (0.4, 0.45)
    wrists = (np.array([0.38, 0.44]), np.array([0.42, 0.46]))  # both close
    assert is_phone_held(phone, wrists, config) is True


def test_phone_not_held_when_wrists_far():
    config = Config(wrist_phone_threshold=0.15)
    phone = np.array([0.3, 0.3, 0.5, 0.6])  # center (0.4, 0.45)
    wrists = (np.array([0.0, 0.0]), np.array([1.0, 1.0]))  # far away
    assert is_phone_held(phone, wrists, config) is False


def test_phone_held_fallback_when_no_wrists():
    config = Config()
    phone = np.array([0.3, 0.3, 0.5, 0.6])
    wrists = (None, None)
    assert is_phone_held(phone, wrists, config) is True


def test_annotate_frame_returns_frame():
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    bbox = np.array([0.3, 0.3, 0.5, 0.6])
    result = annotate_frame(frame, bbox, detected=True)
    assert result.shape == frame.shape
