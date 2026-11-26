"""Hand tracking with the MediaPipe Tasks API."""
import os
import tempfile
import threading
import time
import urllib.request
from collections import deque
from pathlib import Path

import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_tasks
from mediapipe.tasks.python import vision

from .gestures import GESTURES, GestureStabilizer, recognize

MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
    "hand_landmarker/float16/latest/hand_landmarker.task"
)
MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / "hand_landmarker.task"

CONNECTIONS = (
    (0, 1), (1, 2), (2, 3), (3, 4), (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12), (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (0, 17), (17, 18), (18, 19), (19, 20),
)


def ensure_model():
    """Download the hand model on first run and return its path."""
    if MODEL_PATH.exists():
        return MODEL_PATH
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    handle, temp_name = tempfile.mkstemp(dir=MODEL_PATH.parent, suffix=".part")
    os.close(handle)
    try:
        with urllib.request.urlopen(MODEL_URL, timeout=60) as response:
            Path(temp_name).write_bytes(response.read())
        os.replace(temp_name, MODEL_PATH)
    finally:
        if os.path.exists(temp_name):
            os.remove(temp_name)
    return MODEL_PATH


def create_landmarker(video):
    mode = vision.RunningMode.VIDEO if video else vision.RunningMode.IMAGE
    options = vision.HandLandmarkerOptions(
        base_options=mp_tasks.BaseOptions(model_asset_path=str(ensure_model())),
        running_mode=mode,
        num_hands=2,
        min_hand_detection_confidence=0.5,
    )
    return vision.HandLandmarker.create_from_options(options)


def annotate(frame_bgr, result):
    """Draw hands on the frame and return the first recognised gesture."""
    height, width = frame_bgr.shape[:2]
    found = None
    for hand in result.hand_landmarks:
        points = [(lm.x * width, lm.y * height) for lm in hand]
        pixels = [(int(x), int(y)) for x, y in points]
        for start, end in CONNECTIONS:
            cv2.line(frame_bgr, pixels[start], pixels[end], (191, 212, 45), 2, cv2.LINE_AA)
        for pixel in pixels:
            cv2.circle(frame_bgr, pixel, 4, (255, 255, 255), -1, cv2.LINE_AA)
        found = found or recognize(points)
    if found:
        label = GESTURES[found].meaning
        (text_w, _), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)
        cv2.rectangle(frame_bgr, (10, 10), (text_w + 34, 52), (42, 23, 15), -1)
        cv2.putText(frame_bgr, label, (22, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                    (191, 212, 45), 2, cv2.LINE_AA)
    return found


def to_mp_image(frame_bgr):
    rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    return mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)


class LiveSession:
    """State shared between the video thread and the Streamlit script."""

    def __init__(self):
        self._lock = threading.Lock()
        self._landmarker = create_landmarker(video=True)
        self._stabilizer = GestureStabilizer()
        self._events = deque(maxlen=20)
        self._last_timestamp = 0
        self.current = None
        self.error = None

    def set_hold_seconds(self, seconds):
        self._stabilizer.hold_seconds = seconds

    def process(self, frame_bgr):
        """Process one camera frame (called from the video thread)."""
        frame_bgr = cv2.flip(frame_bgr, 1)  # mirror, like a selfie camera
        try:
            with self._lock:
                # VIDEO mode requires strictly increasing timestamps.
                timestamp = max(int(time.monotonic() * 1000), self._last_timestamp + 1)
                self._last_timestamp = timestamp
                result = self._landmarker.detect_for_video(to_mp_image(frame_bgr), timestamp)
                self.current = annotate(frame_bgr, result)
                event = self._stabilizer.update(self.current, time.monotonic())
                if event:
                    self._events.append(event)
        except Exception as error:  # surfaced in the UI instead of failing silently
            self.error = str(error)
        return frame_bgr

    def pop_events(self):
        with self._lock:
            events = list(self._events)
            self._events.clear()
        return events
