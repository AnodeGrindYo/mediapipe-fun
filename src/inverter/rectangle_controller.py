from __future__ import annotations
from typing import Optional, List
from .geometry import Point, Rect
from .smoothing import EMASmoother
from .config import Config

class RectangleController:
    def __init__(self, cfg: Config) -> None:
        self.cfg = cfg
        self._smooth1 = EMASmoother(cfg.smooth_alpha)
        self._smooth2 = EMASmoother(cfg.smooth_alpha)
        self._last_rect: Optional[Rect] = None

    def reset(self) -> None:
        self._smooth1.reset()
        self._smooth2.reset()
        self._last_rect = None

    def update(self, tips: List[Point], w: int, h: int) -> Optional[Rect]:
        if len(tips) >= 2:
            p1 = self._smooth1.update(tips[0])
            p2 = self._smooth2.update(tips[1])
            rect = Rect(p1.x, p1.y, p2.x, p2.y).ordered().clamp(w, h)
            if rect.valid(self.cfg.min_rect_size):
                self._last_rect = rect
        return self._last_rect
