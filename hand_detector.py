# hand_detector.py
# Deteccion de mano con MediaPipe. Devuelve y_norm y dibuja esqueleto (ASCII).

import cv2
import settings

try:
    import mediapipe as mp
    _MP = True
except Exception:
    _MP = False

class HandDetector:
    def __init__(self):
        self.enabled = _MP
        self._ready = False
        self._last_y_norm = None
        self._stable = 0

        self.alpha = float(getattr(settings, "SKELETON_ALPHA", 0.7))
        self.stable_frames = int(getattr(settings, "SKELETON_STABLE_FRAMES", 3))

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
            min_tracking_confidence=0.6
        )
        self._ready = True

    def process(self, frame_bgr):
        if not self.enabled:
            return None, None, False
        self._ensure()
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        res = self.hands.process(rgb)
        if not res.multi_hand_landmarks:
            self._stable = max(0, self._stable - 1)
            return None, None, False
        lm = res.multi_hand_landmarks[0]
        h = frame_bgr.shape[0]
        y_px = int(lm.landmark[9].y * h)  # middle_mcp aprox
        y_norm = max(0.0, min(1.0, y_px / max(1, h)))
        self._last_y_norm = y_norm
        self._stable = min(self.stable_frames + 2, self._stable + 1)
        return y_norm, lm, True

    def draw_skeleton(self, frame_bgr, landmarks):
        if not self.enabled or landmarks is None:
            return
        overlay = frame_bgr.copy()
        self.mp_draw.draw_landmarks(
            overlay, landmarks, self.mp_hands.HAND_CONNECTIONS,
            self.mp_styles.get_default_hand_landmarks_style(),
            self.mp_styles.get_default_hand_connections_style()
        )
        a = max(0.0, min(1.0, self.alpha))
        cv2.addWeighted(overlay, a, frame_bgr, 1.0 - a, 0, frame_bgr)