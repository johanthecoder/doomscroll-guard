from __future__ import annotations
import logging
import os
import time
from datetime import datetime

import cv2
import numpy as np

_log = logging.getLogger(__name__)


def capture_shame_frame() -> np.ndarray | None:
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()
    return frame if ret else None


def annotate_shame(frame: np.ndarray) -> np.ndarray:
    out = frame.copy()
    h, w = out.shape[:2]
    overlay = out.copy()
    cv2.rectangle(overlay, (0, h // 2 - 60), (w, h // 2 + 60), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.6, out, 0.4, 0, out)
    cv2.putText(
        out, "GET BACK TO WORK",
        (w // 8, h // 2 + 20),
        cv2.FONT_HERSHEY_DUPLEX, 1.4, (0, 0, 255), 3,
    )
    return out


def save_shame_shot(frame: np.ndarray, shots_dir: str) -> str:
    os.makedirs(shots_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    path = os.path.join(shots_dir, f"{ts}.jpg")
    cv2.imwrite(path, frame)
    return path


def show_shame(shots_dir: str = "~/.doomscroll/shame_shots") -> str | None:
    frame = capture_shame_frame()
    if frame is None:
        _log.warning("show_shame: could not capture webcam frame")
        return None
    annotated = annotate_shame(frame)
    expanded_dir = os.path.expanduser(shots_dir)
    path = save_shame_shot(annotated, expanded_dir)
    try:
        cv2.namedWindow("CAUGHT", cv2.WND_PROP_FULLSCREEN)
        cv2.setWindowProperty("CAUGHT", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        cv2.imshow("CAUGHT", annotated)
        cv2.waitKey(3000)
        cv2.destroyWindow("CAUGHT")
    except Exception as e:
        _log.warning("show_shame display error: %s", e)
    return path
