import numpy as np
from .geometry import Rect

class ROIInverter:
    @staticmethod
    def invert_inplace(frame: np.ndarray, rect: Rect) -> None:
        roi = frame[rect.y1:rect.y2, rect.x1:rect.x2]
        frame[rect.y1:rect.y2, rect.x1:rect.x2] = 255 - roi
