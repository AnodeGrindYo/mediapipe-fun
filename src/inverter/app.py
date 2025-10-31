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

    def show(self, frame: np.ndarray) -> None:
        cv2.imshow(self.cfg.window_title, frame)

    def handle_key(self, key: int) -> bool:
        """Return True to continue, False to exit."""
        if key == ord("q"):
            return False
        if key == ord("r"):
            self.rect_ctrl.reset()
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
                if not self.handle_key(cv2.waitKey(1) & 0xFF):
                    break
        finally:
            self.close()

    # --- Resource management ---

    def close(self) -> None:
        self.cap.release()
        self.tracker.close()
        cv2.destroyAllWindows()
