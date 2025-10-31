import cv2
from typing import List
from .geometry import Point, Rect

class OverlayDrawer:
    def __init__(self) -> None:
        self._font = cv2.FONT_HERSHEY_SIMPLEX

    def draw_points(self, frame, pts: List[Point]) -> None:
        for p in pts:
            cv2.circle(frame, (p.x, p.y), 8, (255, 255, 255), 2)
            cv2.circle(frame, (p.x, p.y), 4, (0, 255, 255), -1)

    def draw_rect(self, frame, rect: Rect) -> None:
        cv2.rectangle(frame, (rect.x1, rect.y1), (rect.x2, rect.y2), (0, 200, 255), 2)
        cv2.circle(frame, (rect.x1, rect.y1), 6, (0, 200, 255), -1)
        cv2.circle(frame, (rect.x2, rect.y2), 6, (0, 200, 255), -1)

    def hud(self, frame, msg_top: str, msg_bottom: str) -> None:
        h = frame.shape[0]
        cv2.putText(frame, msg_top, (10, 24), self._font, 0.6, (180, 220, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, msg_bottom, (10, h - 12), self._font, 0.6, (180, 220, 255), 2, cv2.LINE_AA)

    def fps(self, frame, fps: float) -> None:
        cv2.putText(frame, f"{fps:.1f} FPS", (10, 48), self._font, 0.6, (120, 255, 120), 2, cv2.LINE_AA)
