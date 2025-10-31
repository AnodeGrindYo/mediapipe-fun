from __future__ import annotations
from dataclasses import dataclass

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
        a = sorted([self.x1, self.x2])
        b = sorted([self.y1, self.y2])
        return Rect(a[0], b[0], a[1], b[1])

    def clamp(self, w: int, h: int) -> "Rect":
        x1 = max(0, min(self.x1, w - 1))
        x2 = max(0, min(self.x2, w - 1))
        y1 = max(0, min(self.y1, h - 1))
        y2 = max(0, min(self.y2, h - 1))
        return Rect(x1, y1, x2, y2).ordered()

    def valid(self, min_size: int) -> bool:
        return (self.x2 - self.x1) >= min_size and (self.y2 - self.y1) >= min_size
