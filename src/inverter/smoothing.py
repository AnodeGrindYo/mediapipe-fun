from __future__ import annotations
from typing import Optional
from .geometry import Point

class EMASmoother:
    def __init__(self, alpha: float) -> None:
        if not (0.0 <= alpha <= 1.0):
            raise ValueError("alpha must be in [0,1]")
        self.alpha = alpha
        self._prev: Optional[Point] = None

    def update(self, new_p: Point) -> Point:
        if self._prev is None:
            self._prev = new_p
            return new_p
        px, py = self._prev.x, self._prev.y
        nx, ny = new_p.x, new_p.y
        sx = int(px * (1 - self.alpha) + nx * self.alpha)
        sy = int(py * (1 - self.alpha) + ny * self.alpha)
        self._prev = Point(sx, sy)
        return self._prev

    def reset(self) -> None:
        self._prev = None
