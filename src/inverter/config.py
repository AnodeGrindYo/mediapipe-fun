from __future__ import annotations
from dataclasses import dataclass

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
