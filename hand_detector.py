# Archivo: hand_detector.py - Deteccion de mano con MediaPipe (estabilizada)
# ASCII puro

import cv2
import mediapipe as mp
import numpy as np
import settings


class HandDetector:
    def __init__(self):
        self.hands = mp.solutions.hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=settings.DETECTION_CONFIDENCE,
            min_tracking_confidence=settings.TRACKING_CONFIDENCE,
            model_complexity=1,
        )
        self.drawer = mp.solutions.drawing_utils
        self._y_ema = settings.SCREEN_HEIGHT // 2
        self._alpha = float(getattr(settings, "HAND_EMA_ALPHA", 0.35))
        self._deadzone = int(getattr(settings, "HAND_DEADZONE_PX", 10))
        self._calib_offset = 0
        self._max_jump_px = settings.SCREEN_HEIGHT * 0.20

    def _stable_y(self, y_raw):
        y_raw = float(np.clip(y_raw + self._calib_offset, 0, settings.SCREEN_HEIGHT))
        if abs(y_raw - self._y_ema) < self._deadzone:
            y_raw = self._y_ema
        if abs(y_raw - self._y_ema) > self._max_jump_px:
            direction = 1.0 if y_raw > self._y_ema else -1.0
            y_raw = self._y_ema + direction * self._max_jump_px
        self._y_ema = (1.0 - self._alpha) * self._y_ema + self._alpha * y_raw
        return int(self._y_ema)

    def process(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self.hands.process(rgb)
        if result.multi_hand_landmarks:
            hand = result.multi_hand_landmarks[0]
            idx = [0, 5, 9, 13, 17]
            ys = [hand.landmark[i].y for i in idx]
            y_mean = float(np.mean(ys))
            y_screen = y_mean * settings.SCREEN_HEIGHT
            y_est = self._stable_y(y_screen)
            landmarks = [(lm.x, lm.y) for lm in hand.landmark]
            return y_est, landmarks, True
        return int(self._y_ema), None, False

    def draw_skeleton(self, frame, landmarks):
        if landmarks is None:
            return
        h, w = frame.shape[:2]
        for (x, y) in landmarks:
            cx, cy = int(x * w), int(y * h)
            cv2.circle(frame, (cx, cy), 3, (0, 255, 0), -1)