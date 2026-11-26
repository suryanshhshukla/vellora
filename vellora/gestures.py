"""Gesture definitions and recognition from 21 MediaPipe hand landmarks.

Pure Python (no camera or MediaPipe needed), so it is easy to test.
"""
from dataclasses import dataclass
from math import dist


@dataclass(frozen=True)
class Gesture:
    emoji: str
    name: str
    meaning: str
    how_to: str
    reply: str


GESTURES = {
    "THUMBS_UP": Gesture("👍", "Thumbs up", "Yes / Good",
                         "Thumb up, other fingers closed.",
                         "Great! I'm glad you agree."),
    "THUMBS_DOWN": Gesture("👎", "Thumbs down", "No / Bad",
                           "Thumb down, other fingers closed.",
                           "I understand you disagree or need something different."),
    "OPEN_PALM": Gesture("✋", "Open palm", "Hello / Stop",
                         "All fingers extended, palm to the camera.",
                         "Hello! How can I help you?"),
    "CLOSED_FIST": Gesture("✊", "Closed fist", "Wait",
                           "All fingers closed into a fist.",
                           "I'll wait for your next instruction."),
    "PEACE_SIGN": Gesture("✌️", "Peace sign", "Peace / Two",
                          "Only index and middle fingers extended.",
                          "Peace! Do you need help with two options?"),
    "POINTING_UP": Gesture("☝️", "Pointing up", "Attention / Question",
                           "Only the index finger, pointing up.",
                           "Do you have a question? I'm listening."),
    "PINCH": Gesture("👌", "Pinch", "Small / Little",
                     "Touch the thumb and index fingertips together.",
                     "I understand you're referring to something small or precise."),
}

WRIST = 0
THUMB_MCP, THUMB_IP, THUMB_TIP = 2, 3, 4
INDEX_MCP, INDEX_PIP, INDEX_TIP = 5, 6, 8
MIDDLE_MCP, MIDDLE_PIP, MIDDLE_TIP = 9, 10, 12
RING_PIP, RING_TIP = 14, 16
PINKY_MCP, PINKY_PIP, PINKY_TIP = 17, 18, 20


def recognize(points):
    """Return a gesture key, or None.

    ``points`` is a sequence of 21 (x, y) pairs in *pixel* coordinates,
    with y increasing downwards.
    """
    if len(points) != 21:
        return None
    wrist = points[WRIST]
    palm = dist(wrist, points[MIDDLE_MCP])
    if palm == 0:
        return None

    def extended(tip, pip):
        # Distance from the wrist works even when the hand is tilted.
        return dist(points[tip], wrist) > dist(points[pip], wrist) * 1.1

    index = extended(INDEX_TIP, INDEX_PIP)
    middle = extended(MIDDLE_TIP, MIDDLE_PIP)
    ring = extended(RING_TIP, RING_PIP)
    pinky = extended(PINKY_TIP, PINKY_PIP)

    # Pinch comes first because the index finger is only partly bent.
    touching = dist(points[THUMB_TIP], points[INDEX_TIP]) < palm * 0.3
    index_reaching = dist(points[INDEX_TIP], wrist) > palm * 1.2
    if touching and (middle or index_reaching):
        return "PINCH"

    if index and middle and ring and pinky:
        return "OPEN_PALM"
    if index and middle and not ring and not pinky:
        return "PEACE_SIGN"
    if index and not (middle or ring or pinky):
        if points[INDEX_TIP][1] < points[INDEX_MCP][1] - palm * 0.4:
            return "POINTING_UP"
        return None

    if not (index or middle or ring or pinky):
        thumb_out = (
            dist(points[THUMB_TIP], points[PINKY_MCP])
            > dist(points[THUMB_IP], points[PINKY_MCP]) * 1.05
            and dist(points[THUMB_TIP], points[INDEX_MCP]) > palm * 0.5
        )
        if thumb_out:
            dx = points[THUMB_TIP][0] - points[THUMB_MCP][0]
            dy = points[THUMB_TIP][1] - points[THUMB_MCP][1]
            if abs(dy) > abs(dx):
                return "THUMBS_UP" if dy < 0 else "THUMBS_DOWN"
        return "CLOSED_FIST"
    return None


class GestureStabilizer:
    """Report a gesture once, after it has been held steadily.

    The same gesture is reported again only after the hand has changed or
    disappeared for ``release_seconds``.
    """

    def __init__(self, hold_seconds=0.8, release_seconds=0.5):
        self.hold_seconds = hold_seconds
        self.release_seconds = release_seconds
        self.reset()

    def reset(self):
        self._candidate = None
        self._since = 0.0
        self._reported = None
        self._last_seen_reported = 0.0

    def update(self, gesture, now):
        if gesture != self._candidate:
            self._candidate, self._since = gesture, now
        if self._reported is not None:
            if gesture == self._reported:
                self._last_seen_reported = now
            elif now - self._last_seen_reported >= self.release_seconds:
                self._reported = None
        if (gesture is not None and gesture != self._reported
                and now - self._since >= self.hold_seconds):
            self._reported = gesture
            self._last_seen_reported = now
            return gesture
        return None
