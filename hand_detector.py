# Archivo: hand_detector.py - deteccion de mano con MediaPipe (con fallback)
# ASCII puro

import cv2
import numpy as np
import settings

try:
    import mediapipe as mp
    _MP_OK = True
except Exception:
    mp = None
    _MP_OK = False


class HandDetector:
    def __init__(self):
        self.available = _MP_OK
        self._y_ema = settings.SCREEN_HEIGHT // 2
        self._alpha = float(getattr(settings, "HAND_EMA_ALPHA", 0.38))
        self._deadzone = int(getattr(settings, "HAND_DEADZONE_PX", 12))
        self._calib_offset = 0.0
        self._max_jump_px = settings.SCREEN_HEIGHT * 0.22
        self._sim_t = 0.0  # para modo simulacion

        if self.available:
            self.hands = mp.solutions.hands.Hands(
                static_image_mode=False,
                max_num_hands=1,
                min_detection_confidence=getattr(settings, "DETECTION_CONFIDENCE", 0.55),
                min_tracking_confidence=getattr(settings, "TRACKING_CONFIDENCE", 0.55),
                model_complexity=1,
            )
            self.drawer = mp.solutions.drawing_utils
        else:
            self.hands = None
            self.drawer = None

    def calibrate_center(self):
        # al presionar 'c', fija el centro actual como referencia (offset)
        self._calib_offset = float(settings.SCREEN_HEIGHT / 2.0 - self._y_ema)

    def _stable_y(self, y_raw):
        y_raw = float(np.clip(y_raw + self._calib_offset, 0, settings.SCREEN_HEIGHT))
        if abs(y_raw - self._y_ema) < self._deadzone:
            y_raw = self._y_ema
        if abs(y_raw - self._y_ema) > self._max_jump_px:
            direction = 1.0 if y_raw > self._y_ema else -1.0
            y_raw = self._y_ema + direction * self._max_jump_px
        self._y_ema = (1.0 - self._alpha) * self._y_ema + self._alpha * y_raw
        return int(self._y_ema)

    def _simulate(self, dt):
        # mano simulada (modo sin mediapipe o sin camara estable)
        self._sim_t += dt
        y = settings.SCREEN_HEIGHT / 2.0 + np.sin(self._sim_t * 1.2) * (settings.SCREEN_HEIGHT * 0.25)
        return int(np.clip(y, 0, settings.SCREEN_HEIGHT)), None, True

    def process(self, frame, dt=1.0 / 60.0):
        if not self.available:
            return self._simulate(dt)

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
        return None, None, False

    def draw_skeleton(self, frame, landmarks):
        if not self.available or landmarks is None:
            return
        h, w = frame.shape[:2]
        for (x, y) in landmarks:
            cx, cy = int(x * w), int(y * h)
            cv2.circle(frame, (cx, cy), 3, (0, 255, 0), -1)
