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
    # keep the exception hidden from import time but provide a helpful hint
    # (agents should avoid raising here; rely on available flag)


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
        self._calib_offset = float(settings.SCREEN_HEIGHT / 2.0 - float(self._y_ema))

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
        y_c = int(np.clip(y, 0, settings.SCREEN_HEIGHT))
        # create simple fake landmarks (palm center + 5 fingertips-ish) for visualization
        h = settings.SCREEN_HEIGHT
        landmarks = [
            (0.5, y_c / h),
            (0.45, (y_c - 0.05 * h) / h),
            (0.55, (y_c - 0.05 * h) / h),
            (0.40, (y_c + 0.05 * h) / h),
            (0.60, (y_c + 0.05 * h) / h),
        ]
        # keep EMA stable
        self._y_ema = y_c
        return y_c, landmarks, True

    def process(self, frame, dt=1.0 / 60.0):
        if not self.available:
            return self._simulate(dt)

        try:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = self.hands.process(rgb)
        except Exception:
            # if mediapipe fails at runtime (protobuf mismatch, camera issues), fall back to simulate
            return self._simulate(dt)
        if result.multi_hand_landmarks:
            hand = result.multi_hand_landmarks[0]
            idx = [0, 5, 9, 13, 17]
            ys = [hand.landmark[i].y for i in idx]
            y_mean = float(np.mean(ys))
            y_screen = y_mean * settings.SCREEN_HEIGHT
            y_est = self._stable_y(y_screen)
            landmarks = [(lm.x, lm.y) for lm in hand.landmark]
            return y_est, landmarks, True
        # no detection this frame: return last stable EMA so player keeps following
        return int(self._y_ema), None, False

    def draw_skeleton(self, frame, landmarks):
        # Draw landmarks; if none, draw a simple indicator at last EMA
        h, w = frame.shape[:2]
        if landmarks is None:
            # draw a small circle at right-side x and EMA y to indicate hand position
            cx = int(w * 0.75)
            cy = int(self._y_ema)
            cv2.circle(frame, (cx, cy), 6, (0, 200, 80), -1)
            cv2.putText(frame, "hand", (cx + 10, cy + 5), settings.FONT, 0.5, (200, 255, 200), 1, cv2.LINE_AA)
            return

        for (x, y) in landmarks:
            try:
                cx, cy = int(x * w), int(y * h)
            except Exception:
                continue
            cv2.circle(frame, (cx, cy), 4, (0, 255, 0), -1)

        # connect first point to others for a simple palm visualization
        if len(landmarks) >= 2:
            x0, y0 = landmarks[0]
            x0, y0 = int(x0 * w), int(y0 * h)
            for (x, y) in landmarks[1:]:
                cv2.line(frame, (x0, y0), (int(x * w), int(y * h)), (0, 200, 100), 1)
