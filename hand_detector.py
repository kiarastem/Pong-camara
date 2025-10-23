# hand_detector.py
# Detector de mano con MediaPipe. Devuelve:
#  - y_control: posicion Y (pixeles) para mover la paleta
#  - landmarks_px: lista de puntos (x,y) en pixeles
#  - handedness: "Left" o "Right"
# Incluye dibujo del esqueleto con alpha.
# Texto en espanol sin tildes (ASCII).

import cv2
import numpy as np
import time
import settings

# MediaPipe es opcional: si no existe, el detector queda deshabilitado
try:
    import mediapipe as mp
    _MP_AVAILABLE = True
except Exception:
    _MP_AVAILABLE = False


class HandDetector:
    """
    Uso:
      detector = HandDetector()
      y, pts, handed = detector.process(frame_bgr)
      if pts:
          detector.draw_skeleton(frame_bgr, pts)

    Diseno:
      - Calcula y_control como promedio entre wrist (0) y MIDDLE_MCP (9)
        para mayor estabilidad vertical.
      - Usa un contador de estabilidad (SKELETON_STABLE_FRAMES) para
        cambiar el color del esqueleto cuando hay deteccion estable.
      - Parametros visuales y de confianza se leen de settings.py.
    """

    def __init__(self):
        self.enabled = _MP_AVAILABLE
        self.last_visible = False
        self._stable_counter = 0
        self._last_y = None

        # Lee parametros de settings con valores por defecto seguros
        self.min_det_conf = float(getattr(settings, "DETECTION_CONFIDENCE", 0.5))
        self.min_trk_conf = float(getattr(settings, "TRACKING_CONFIDENCE", 0.5))
        self.skel_alpha   = float(getattr(settings, "SKELETON_ALPHA", 0.7))
        self.skel_thick   = int(getattr(settings, "SKELETON_THICKNESS", 2))
        self.skel_radius  = int(getattr(settings, "SKELETON_RADIUS", 5))
        self.color_ok     = tuple(getattr(settings, "SKELETON_COLOR_DETECTED",
                                          getattr(settings, "SKELETON_COLOR", (0, 255, 255))))
        self.color_lost   = tuple(getattr(settings, "SKELETON_COLOR_LOST", (200, 200, 200)))
        self.stable_frames = int(getattr(settings, "SKELETON_STABLE_FRAMES", 3))

        if not self.enabled:
            print("WARN: MediaPipe no disponible. La deteccion de mano estara desactivada.")
            self.hands = None
            self.connections = None
            return

        mp_solutions = mp.solutions
        self.mp_hands = mp_solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_styles = mp.solutions.drawing_styles

        # Inicializa MediaPipe Hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=self.min_det_conf,
            min_tracking_confidence=self.min_trk_conf,
            model_complexity=1
        )
        self.connections = self.mp_hands.HAND_CONNECTIONS

    # --------------------------------------------------------
    # Procesamiento
    # --------------------------------------------------------
    def process(self, frame_bgr):
        """
        Procesa un frame BGR y devuelve (y_control, landmarks_px, handedness).
        y_control: int | None
        landmarks_px: list[(x,y)] | None
        handedness: str | None
        """
        if not self.enabled:
            return None, None, None

        h, w = frame_bgr.shape[:2]
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        res = self.hands.process(frame_rgb)

        if not res.multi_hand_landmarks or not res.multi_handedness:
            # perdida de deteccion: baja contador y actualiza estado estable
            self._stable_counter = max(0, self._stable_counter - 1)
            self.last_visible = self._stable_counter >= self.stable_frames
            return None, None, None

        hand_landmarks = res.multi_hand_landmarks[0]
        handed = res.multi_handedness[0].classification[0].label  # "Left" o "Right"

        # convierte landmarks a pixeles
        pts = []
        for lm in hand_landmarks.landmark:
            x = int(lm.x * w)
            y = int(lm.y * h)
            pts.append((x, y))

        # posicion Y de control (promedio entre wrist y MIDDLE_MCP si existe)
        if len(pts) >= 10:
            y_control = int((pts[0][1] + pts[9][1]) * 0.5)
        else:
            y_control = int(pts[0][1])

        # marca estabilidad
        self._stable_counter = min(self.stable_frames + 2, self._stable_counter + 1)
        self.last_visible = self._stable_counter >= self.stable_frames
        self._last_y = y_control

        return y_control, pts, handed

    # --------------------------------------------------------
    # Dibujo del esqueleto
    # --------------------------------------------------------
    def draw_skeleton(self, frame_bgr, landmarks_px, alpha=None, color=None):
        """
        Dibuja el esqueleto con alpha sobre frame_bgr.
        - landmarks_px: lista de (x,y) en pixeles
        - alpha: float opcional (0..1); usa settings si es None
        - color: BGR opcional; si None, usa color_ok o color_lost segun estabilidad
        """
        if landmarks_px is None or len(landmarks_px) == 0:
            return

        a = self.skel_alpha if alpha is None else float(alpha)
        a = max(0.0, min(1.0, a))

        if color is None:
            col = self.color_ok if self.last_visible else self.color_lost
        else:
            col = tuple(int(c) for c in color)

        overlay = frame_bgr.copy()

        # Dibuja conexiones (si hay MediaPipe); si no, usa un conjunto basico
        if _MP_AVAILABLE and self.connections is not None:
            for (i, j) in self.connections:
                if i < len(landmarks_px) and j < len(landmarks_px):
                    p1 = landmarks_px[i]
                    p2 = landmarks_px[j]
                    cv2.line(overlay, p1, p2, col, self.skel_thick, cv2.LINE_AA)
        else:
            basic = [
                (0, 1), (1, 2), (2, 3), (3, 4),      # pulgar
                (0, 5), (5, 6), (6, 7), (7, 8),      # indice
                (0, 9), (9,10), (10,11), (11,12),    # medio
                (0,13), (13,14), (14,15), (15,16),   # anular
                (0,17), (17,18), (18,19), (19,20)    # menique
            ]
            n = len(landmarks_px)
            for (i, j) in basic:
                if i < n and j < n:
                    cv2.line(overlay, landmarks_px[i], landmarks_px[j], col, self.skel_thick, cv2.LINE_AA)

        # Dibuja puntos
        for (x, y) in landmarks_px:
            cv2.circle(overlay, (int(x), int(y)), self.skel_radius, col, -1, cv2.LINE_AA)

        # Mezcla con alpha
        cv2.addWeighted(overlay, a, frame_bgr, 1.0 - a, 0, frame_bgr)