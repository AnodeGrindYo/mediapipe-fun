from __future__ import annotations
from typing import Optional, Tuple, List
import time
import cv2
import numpy as np

from .config import Config
from .geometry import Rect, Point
from .hand_tracking import HandTracker
from .overlay import OverlayDrawer
from .rectangle_controller import RectangleController
from .effects import ROIInverter

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

        # Create a resizable window so the user can drag to any size
        cv2.namedWindow(self.cfg.window_title, cv2.WINDOW_NORMAL)
        # Provide an initial reasonable size (will adapt automatically later)
        cv2.resizeWindow(self.cfg.window_title, 960, 540)

    # --- Small, focused helpers ---

    def read_frame(self) -> Optional[np.ndarray]:
        ok, frame = self.cap.read()
        if not ok:
            return None
        if self.cfg.mirror_frame:
            frame = cv2.flip(frame, 1)
        return frame

    def detect_tips(self, frame: np.ndarray) -> List[Point]:
        return self.tracker.process(frame)

    def compute_rect(self, tips: List[Point], shape: Tuple[int, int, int]) -> Optional[Rect]:
        h, w = shape[0], shape[1]
        return self.rect_ctrl.update(tips, w, h)

    def apply_effects(self, frame: np.ndarray, rect: Optional[Rect]) -> None:
        if rect:
            ROIInverter.invert_inplace(frame, rect)

    def draw_overlays(self, frame: np.ndarray, tips: List[Point], rect: Optional[Rect]) -> None:
        self.drawer.draw_points(frame, tips)
        if rect:
            self.drawer.draw_rect(frame, rect)
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

    def _current_window_size(self) -> Tuple[int, int]:
        """Return (width, height) of the HighGUI window, falling back to a default."""
        try:
            # OpenCV >= 4.5 provides getWindowImageRect
            x, y, w, h = cv2.getWindowImageRect(self.cfg.window_title)
            # When window is minimized, sizes may be 0
            if w <= 0 or h <= 0:
                return (960, 540)
            return (w, h)
        except Exception:
            # Fallback if function not available
            return (960, 540)

    def _fit_to_window(self, frame: np.ndarray) -> np.ndarray:
        """Scale frame to current window size while preserving aspect ratio (letterbox)."""
        target_w, target_h = self._current_window_size()
        if target_w <= 0 or target_h <= 0:
            return frame
        h, w = frame.shape[:2]
        scale = min(target_w / w, target_h / h)
        new_w, new_h = max(1, int(w * scale)), max(1, int(h * scale))
        resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

        # Letterbox (center) into a canvas of target size
        if new_w == target_w and new_h == target_h:
            return resized
        canvas = np.zeros((target_h, target_w, 3), dtype=frame.dtype)
        off_x = (target_w - new_w) // 2
        off_y = (target_h - new_h) // 2
        canvas[off_y:off_y+new_h, off_x:off_x+new_w] = resized
        return canvas

    def show(self, frame: np.ndarray) -> None:
        # Adapt display to current window size
        adapted = self._fit_to_window(frame)
        cv2.imshow(self.cfg.window_title, adapted)

    def handle_key_or_close(self) -> bool:
        """Return True to continue, False to exit. Handles keypress and window close (X)."""
        # 1) Handle key
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            return False
        if key == ord("r"):
            self.rect_ctrl.reset()

        # 2) Detect user closing the window with the [X]
        # If WND_PROP_VISIBLE < 1, the window has been closed.
        if cv2.getWindowProperty(self.cfg.window_title, cv2.WND_PROP_VISIBLE) < 1:
            return False
        return True

    # --- Main loop ---

    def run(self) -> None:
        try:
            while True:
                frame = self.read_frame()
                if frame is None:
                    break
                tips = self.detect_tips(frame)
                rect = self.compute_rect(tips, frame.shape)
                self.apply_effects(frame, rect)
                self.update_fps()
                self.draw_overlays(frame, tips, rect)
                self.show(frame)
                if not self.handle_key_or_close():
                    break
        finally:
            self.close()

    # --- Resource management ---

    def close(self) -> None:
        self.cap.release()
        self.tracker.close()
        cv2.destroyAllWindows()
