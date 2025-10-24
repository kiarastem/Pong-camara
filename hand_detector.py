# hand_detector.py — Deteccion de mano con MediaPipe (opcional). Devuelve (y_norm, landmarks, valid)

import cv2
import settings

try:
    import mediapipe as mp
    _MP = True
except Exception:
    _MP = False

def clamp(v, a, b):
    return max(a, min(b, v))

class HandDetector:
    def __init__(self):
        self.enabled = _MP
        self._ready = False

        # suavizado
        self.hand_ema = None
        self.hand_ema_alpha = float(getattr(settings, "HAND_EMA_ALPHA", 0.28))

        if self.enabled:
            self.mp_hands = mp.solutions.hands
            self.mp_draw = mp.solutions.drawing_utils
            self.mp_styles = mp.solutions.drawing_styles

    def _ensure(self):
        if self._ready or not self.enabled:
            return
        self.hands = self.mp_hands.Hands(
            max_num_hands=1,
            min_detection_confidence=settings.DETECTION_CONFIDENCE,
            min_tracking_confidence=settings.TRACKING_CONFIDENCE
        )
        self._ready = True

    def process(self, frame_bgr):
        if not self.enabled:
            return None, None, False
        self._ensure()
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        res = self.hands.process(rgb)
        if not res.multi_hand_landmarks:
            return None, None, False

        lm = res.multi_hand_landmarks[0]
        h = frame_bgr.shape[0]
        y_px = int(lm.landmark[9].y * h)  # middle_mcp aprox
        y_norm = clamp(y_px / max(1, h), 0.0, 1.0)

        # EMA para suavizar
        if self.hand_ema is None:
            self.hand_ema = float(y_norm)
        else:
            a = self.hand_ema_alpha
            self.hand_ema = (1.0 - a) * float(self.hand_ema) + a * float(y_norm)

        return float(self.hand_ema), lm, True

    def draw_skeleton(self, frame_bgr, landmarks):
        if not self.enabled or landmarks is None:
            return
        overlay = frame_bgr.copy()
        self.mp_draw.draw_landmarks(
            overlay, landmarks, self.mp_hands.HAND_CONNECTIONS,
            self.mp_styles.get_default_hand_landmarks_style(),
            self.mp_styles.get_default_hand_connections_style()
        )
        cv2.addWeighted(overlay, 0.85, frame_bgr, 0.15, 0, frame_bgr)