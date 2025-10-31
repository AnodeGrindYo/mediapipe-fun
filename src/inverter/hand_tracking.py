from __future__ import annotations
from typing import List
import cv2
import numpy as np
import mediapipe as mp
from .geometry import Point
from .config import Config

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
