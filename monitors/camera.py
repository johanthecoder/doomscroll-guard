from __future__ import annotations
import logging
import time
import threading
import math
from typing import Callable

import cv2
import numpy as np

from config import Config
from types_ import CameraViolation

_log = logging.getLogger(__name__)


def is_phone_held(
    phone_box: np.ndarray,
    wrists: tuple[np.ndarray | None, np.ndarray | None],
    config: Config,
) -> bool:
    if phone_box is None:
        return False
    x1, y1, x2, y2 = phone_box
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    left_wrist, right_wrist = wrists

    if left_wrist is None and right_wrist is None:
        return True  # no pose data — count phone as held

    for wrist in (left_wrist, right_wrist):
        if wrist is not None:
            dist = math.sqrt((wrist[0] - cx) ** 2 + (wrist[1] - cy) ** 2)
            if dist < config.wrist_phone_threshold:
                return True
    return False


def annotate_frame(
    frame: np.ndarray,
    bbox: np.ndarray | None,
    detected: bool,
) -> np.ndarray:
    out = frame.copy()
    h, w = out.shape[:2]
    if detected and bbox is not None:
        x1, y1, x2, y2 = bbox
        pt1 = (int(x1 * w), int(y1 * h))
        pt2 = (int(x2 * w), int(y2 * h))
        cv2.rectangle(out, pt1, pt2, (0, 0, 255), 2)
        cv2.putText(out, "PHONE DETECTED", pt1, cv2.FONT_HERSHEY_DUPLEX, 0.7, (0, 0, 255), 2)
    return out


def _extract_phone(results) -> np.ndarray | None:
    for r in results:
        for box in r.boxes:
            if int(box.cls[0].item()) == 67:
                return box.xyxyn[0].cpu().numpy()
    return None


def _extract_wrists(results) -> tuple[np.ndarray | None, np.ndarray | None]:
    for r in results:
        if r.keypoints is not None:
            try:
                kpts = r.keypoints.xyn[0].cpu().numpy()
                return kpts[9], kpts[10]
            except Exception:
                pass
    return None, None


class CameraMonitor:
    def __init__(self, config: Config, on_violation: Callable[[CameraViolation], None]):
        self._config = config
        self._on_violation = on_violation
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self.latest_frame: np.ndarray | None = None
        self._model_detect = None
        self._model_pose = None

    def _load_models(self) -> None:
        from ultralytics import YOLO
        self._model_detect = YOLO("models/yolo11n.pt")
        self._model_pose = YOLO("models/yolo11n-pose.pt")

    def start(self) -> None:
        with self._lock:
            if self._thread and self._thread.is_alive():
                return
            self._stop.clear()
            self._thread = threading.Thread(target=self._loop, daemon=True)
            self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        with self._lock:
            thread = self._thread
        if thread:
            thread.join(timeout=5)

    def _loop(self) -> None:
        try:
            self._load_models()
        except Exception as e:
            _log.error("Failed to load YOLO models: %s", e)
            return
        cap = cv2.VideoCapture(0)
        try:
            while not self._stop.is_set():
                ret, frame = cap.read()
                if not ret:
                    self._stop.wait(0.5)
                    continue
                self._process_frame(frame)
                self._stop.wait(0.2)
        finally:
            cap.release()

    def _process_frame(self, frame: np.ndarray) -> None:
        try:
            det_results = self._model_detect(frame, verbose=False, conf=0.1)
            phone_box = _extract_phone(det_results)

            wrists = (None, None)
            if phone_box is not None:
                pose_results = self._model_pose(frame, verbose=False)
                wrists = _extract_wrists(pose_results)

            held = is_phone_held(phone_box, wrists, self._config)
            self.latest_frame = annotate_frame(frame, phone_box, held)

            if held:
                wrist_dist = 0.0
                if phone_box is not None:
                    cx = (phone_box[0] + phone_box[2]) / 2
                    cy = (phone_box[1] + phone_box[3]) / 2
                    for w in wrists:
                        if w is not None:
                            wrist_dist = math.sqrt((w[0] - cx) ** 2 + (w[1] - cy) ** 2)
                            break
                self._on_violation(CameraViolation(
                    confidence=float(det_results[0].boxes[0].conf[0]) if det_results[0].boxes else 0.0,
                    bbox=tuple(phone_box.tolist()) if phone_box is not None else (0.0, 0.0, 0.0, 0.0),
                    wrist_dist=wrist_dist,
                    timestamp=time.time(),
                ))
        except Exception as e:
            _log.debug("_process_frame() error: %s", e)
