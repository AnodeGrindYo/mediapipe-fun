from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Tuple, List
import cv2
import numpy as np
import mediapipe as mp
import time

# =========================
# Configuration & Types
# =========================

@dataclass(frozen=True)
class Config:
    max_num_hands: int = 2
    detection_confidence: float = 0.6
    tracking_confidence: float = 0.5
    model_complexity: int = 1
    smooth_alpha: float = 0.4
    min_rect_size: int = 3
    camera_index: int = 0
    mirror_frame: bool = True
    draw_landmarks: bool = False
    window_title: str = "Index-Rectangle Inverter (MediaPipe, SRP Refactor)"

@dataclass
class Point:
    x: int
    y: int

@dataclass
class Rect:
    x1: int
    y1: int
    x2: int
    y2: int
    def ordered(self) -> "Rect":
        a = sorted([self.x1, self.x2]); b = sorted([self.y1, self.y2])
        return Rect(a[0], b[0], a[1], b[1])
    def clamp(self, w: int, h: int) -> "Rect":
        x1 = max(0, min(self.x1, w - 1)); x2 = max(0, min(self.x2, w - 1))
        y1 = max(0, min(self.y1, h - 1)); y2 = max(0, min(self.y2, h - 1))
        return Rect(x1, y1, x2, y2).ordered()
    def valid(self, min_size: int) -> bool:
        return (self.x2 - self.x1) >= min_size and (self.y2 - self.y1) >= min_size

# =========================
# Smoothing
# =========================

class EMASmoother:
    def __init__(self, alpha: float) -> None:
        if not (0.0 <= alpha <= 1.0): raise ValueError("alpha must be in [0,1]")
        self.alpha = alpha
        self._prev: Optional[Point] = None
    def update(self, new_p: Point) -> Point:
        if self._prev is None:
            self._prev = new_p; return new_p
        px, py = self._prev.x, self._prev.y
        nx, ny = new_p.x, new_p.y
        sx = int(px * (1 - self.alpha) + nx * self.alpha)
        sy = int(py * (1 - self.alpha) + ny * self.alpha)
        self._prev = Point(sx, sy); return self._prev
    def reset(self) -> None: self._prev = None

# =========================
# Hand Tracking
# =========================

class HandTracker:
    def __init__(self, cfg: Config) -> None:
        self.cfg = cfg
        self._mp_hands = mp.solutions.hands
        self._hands = self._mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=cfg.max_num_hands,
            model_complexity=cfg.model_complexity,
            min_detection_confidence=cfg.detection_confidence,
            min_tracking_confidence=cfg.tracking_confidence,
        )
        self._drawer = mp.solutions.drawing_utils
    def process(self, bgr_frame: np.ndarray) -> List[Point]:
        h, w = bgr_frame.shape[:2]
        rgb = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
        result = self._hands.process(rgb)
        tips: List[Point] = []
        if result.multi_hand_landmarks:
            for hand_lms in result.multi_hand_landmarks[: self.cfg.max_num_hands]:
                lm = hand_lms.landmark[self._mp_hands.HandLandmark.INDEX_FINGER_TIP]
                tips.append(Point(int(lm.x * w), int(lm.y * h)))
                if self.cfg.draw_landmarks:
                    self._drawer.draw_landmarks(
                        bgr_frame, hand_lms, self._mp_hands.HAND_CONNECTIONS
                    )
        return tips
    def close(self) -> None:
        self._hands.close()

# =========================
# Effect (ROI inversion)
# =========================

class ROIInverter:
    @staticmethod
    def invert_inplace(frame: np.ndarray, rect: Rect) -> None:
        roi = frame[rect.y1:rect.y2, rect.x1:rect.x2]
        frame[rect.y1:rect.y2, rect.x1:rect.x2] = 255 - roi

# =========================
# Drawing / Overlay
# =========================

class OverlayDrawer:
    def __init__(self) -> None:
        self._font = cv2.FONT_HERSHEY_SIMPLEX
    def draw_points(self, frame: np.ndarray, pts: List[Point]) -> None:
        for p in pts:
            cv2.circle(frame, (p.x, p.y), 8, (255, 255, 255), 2)
            cv2.circle(frame, (p.x, p.y), 4, (0, 255, 255), -1)
    def draw_rect(self, frame: np.ndarray, rect: Rect) -> None:
        cv2.rectangle(frame, (rect.x1, rect.y1), (rect.x2, rect.y2), (0, 200, 255), 2)
        cv2.circle(frame, (rect.x1, rect.y1), 6, (0, 200, 255), -1)
        cv2.circle(frame, (rect.x2, rect.y2), 6, (0, 200, 255), -1)
    def hud(self, frame: np.ndarray, msg_top: str, msg_bottom: str) -> None:
        h = frame.shape[0]
        cv2.putText(frame, msg_top, (10, 24), self._font, 0.6, (180, 220, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, msg_bottom, (10, h - 12), self._font, 0.6, (180, 220, 255), 2, cv2.LINE_AA)
    def fps(self, frame: np.ndarray, fps: float) -> None:
        cv2.putText(frame, f"{fps:.1f} FPS", (10, 48), self._font, 0.6, (120, 255, 120), 2, cv2.LINE_AA)

# =========================
# Rectangle Controller
# =========================

class RectangleController:
    def __init__(self, cfg: Config) -> None:
        self.cfg = cfg
        self._smooth1 = EMASmoother(cfg.smooth_alpha)
        self._smooth2 = EMASmoother(cfg.smooth_alpha)
        self._last_rect: Optional[Rect] = None
    def reset(self) -> None:
        self._smooth1.reset(); self._smooth2.reset(); self._last_rect = None
    def update(self, tips: List[Point], w: int, h: int) -> Optional[Rect]:
        if len(tips) >= 2:
            p1 = self._smooth1.update(tips[0])
            p2 = self._smooth2.update(tips[1])
            rect = Rect(p1.x, p1.y, p2.x, p2.y).ordered().clamp(w, h)
            if rect.valid(self.cfg.min_rect_size):
                self._last_rect = rect
        return self._last_rect

# =========================
# App Loop (Refactor run)
# =========================

class InverterApp:
    def __init__(self, cfg: Config) -> None:
        self.cfg = cfg
        self.tracker = HandTracker(cfg)
        self.drawer = OverlayDrawer()
        self.rect_ctrl = RectangleController(cfg)
        self.cap = cv2.VideoCapture(cfg.camera_index)
        if not self.cap.isOpened():
            self.tracker.close()
            raise RuntimeError(f"Unable to open camera index {cfg.camera_index}")
        self._last_time = time.time()
        self._fps = 0.0

    # --- Small, focused helpers ---

    def read_frame(self) -> Optional[np.ndarray]:
        ok, frame = self.cap.read()
        if not ok: return None
        if self.cfg.mirror_frame: frame = cv2.flip(frame, 1)
        return frame

    def detect_tips(self, frame: np.ndarray) -> List[Point]:
        return self.tracker.process(frame)

    def compute_rect(self, tips: List[Point], shape: Tuple[int, int, int]) -> Optional[Rect]:
        h, w = shape[0], shape[1]
        return self.rect_ctrl.update(tips, w, h)

    def apply_effects(self, frame: np.ndarray, rect: Optional[Rect]) -> None:
        if rect: ROIInverter.invert_inplace(frame, rect)

    def draw_overlays(self, frame: np.ndarray, tips: List[Point], rect: Optional[Rect]) -> None:
        self.drawer.draw_points(frame, tips)
        if rect: self.drawer.draw_rect(frame, rect)
        self.drawer.hud(
            frame,
            "Montrez vos deux index pour inverser les couleurs dans le rectangle.",
            "[Q] Quitter  [R] Reset",
        )
        self.drawer.fps(frame, self._fps)

    def update_fps(self) -> None:
        now = time.time()
        dt = now - self._last_time
        if dt > 0:
            self._fps = 0.9 * self._fps + 0.1 * (1.0 / dt)
        self._last_time = now

    def show(self, frame: np.ndarray) -> None:
        cv2.imshow(self.cfg.window_title, frame)

    def handle_key(self, key: int) -> bool:
        """Return True to continue, False to exit."""
        if key == ord("q"): return False
        if key == ord("r"): self.rect_ctrl.reset()
        return True

    # --- Main loop now tiny & readable ---

    def run(self) -> None:
        try:
            while True:
                frame = self.read_frame()
                if frame is None: break
                tips = self.detect_tips(frame)
                rect = self.compute_rect(tips, frame.shape)
                self.apply_effects(frame, rect)
                self.update_fps()
                self.draw_overlays(frame, tips, rect)
                self.show(frame)
                if not self.handle_key(cv2.waitKey(1) & 0xFF): break
        finally:
            self.close()

    # --- Resource management ---

    def close(self) -> None:
        self.cap.release()
        self.tracker.close()
        cv2.destroyAllWindows()

# =========================
# Entrypoint
# =========================

def main() -> None:
    cfg = Config()
    app = InverterApp(cfg)
    app.run()

if __name__ == "__main__":
    main()
