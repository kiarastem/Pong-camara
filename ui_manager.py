# Archivo: ui_manager.py - Interfaz educativa (menu, marcador, fx, panel)
# ASCII puro

import time
import cv2
import settings


class UIManager:
    def __init__(self):
        self.rings = []
        self.flash_color_val = None
        self.flash_alpha = 0.0

    # ---------- FX: anillo de impacto ----------
    def spawn_hit_ring(self, x, y):
        self.rings.append({"x": float(x), "y": float(y), "t": time.time()})

    def _draw_rings(self, frame):
        now = time.time()
        survivors = []
        fade_time = float(getattr(settings, "RING_FADE_TIME", 0.45))
        for ring in self.rings:
            age = now - ring["t"]
            if age > fade_time:
                continue
            radius = int(30 + age * 220)
            alpha = max(0.0, 1.0 - age / fade_time)
            color = (0, int(220 * alpha), 255)
            cv2.circle(frame, (int(ring["x"]), int(ring["y"])), radius, color, 2)
            survivors.append(ring)
        self.rings = survivors

    # ---------- FX: flash de pantalla ----------
    def flash_color(self, color):
        self.flash_color_val = tuple(int(c) for c in color)
        self.flash_alpha = 0.8

    def _draw_flash(self, frame):
        if self.flash_color_val is None:
            return
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (frame.shape[1], frame.shape[0]), self.flash_color_val, -1)
        alpha = max(0.0, self.flash_alpha)
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
        self.flash_alpha -= getattr(settings, "FLASH_DECAY_RATE", 0.06)
        if self.flash_alpha <= 0.0:
            self.flash_color_val = None

    # ---------- HUD: marcador ----------
    def draw_score(self, frame, scores):
        text = f"{scores[0]}  |  {scores[1]}"
        cv2.putText(
            frame,
            text,
            (int(settings.SCREEN_WIDTH / 2 - 110), 96),
            settings.FONT,
            settings.FONT_SCALE_SCORE,
            (255, 255, 255),
            settings.FONT_THICKNESS_SCORE,
            cv2.LINE_AA,
        )
        self._draw_rings(frame)
        self._draw_flash(frame)

    # ---------- Menu principal (centrado) ----------
    def draw_menu(self, frame):
        title = "HAND PONG"
        subtitle = "Mueve tu mano para controlar la paleta derecha"
        hint = "Presiona ESPACIO para jugar"

        cv2.putText(
            frame, title,
            (int(settings.SCREEN_WIDTH / 2 - 260), int(settings.SCREEN_HEIGHT / 2 - 80)),
            settings.FONT, 2.4, (255, 255, 255), 5, cv2.LINE_AA
        )
        cv2.putText(
            frame, subtitle,
            (int(settings.SCREEN_WIDTH / 2 - 420), int(settings.SCREEN_HEIGHT / 2 - 20)),
            settings.FONT, 1.0, (220, 220, 220), 2, cv2.LINE_AA
        )
        cv2.putText(
            frame, hint,
            (int(settings.SCREEN_WIDTH / 2 - 300), int(settings.SCREEN_HEIGHT / 2 + 60)),
            settings.FONT, 1.2, (255, 255, 255), 3, cv2.LINE_AA
        )

        # panel de controles al costado derecho
        self.draw_controls_panel(frame)

    # ---------- Panel de controles (estatico) ----------
    def draw_controls_panel(self, frame):
        lines = [
            "Controles",
            "  ESPACIO -> jugar/pausa",
            "  R       -> reiniciar",
            "  ESC     -> salir",
            "  H       -> HUD on/off",
            "  L       -> linea prediccion IA on/off",
            "  I       -> panel educativo on/off",
            "  G       -> pantalla completa",
        ]
        pad_x = 14
        pad_y = 12
        line_h = 22
        text_w = 0
        for s in lines:
            (tw, _), _ = cv2.getTextSize(s, settings.FONT, 0.7, 1)
            text_w = max(text_w, tw)
        panel_w = text_w + pad_x * 2
        panel_h = line_h * len(lines) + pad_y * 2
        x0 = settings.SCREEN_WIDTH - panel_w - 24
        y0 = 24

        overlay = frame.copy()
        cv2.rectangle(overlay, (x0, y0), (x0 + panel_w, y0 + panel_h), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.35, frame, 0.65, 0, frame)

        y = y0 + pad_y + 16
        for i, s in enumerate(lines):
            scale = 0.8 if i == 0 else 0.7
            thick = 2 if i == 0 else 1
            cv2.putText(frame, s, (x0 + pad_x, y), settings.FONT, scale, (235, 235, 235), thick, cv2.LINE_AA)
            y += line_h

    # ---------- Panel educativo inferior ----------
    def draw_edu_panel(self, frame, text):
        panel_h = 96
        overlay = frame.copy()
        cv2.rectangle(
            overlay,
            (0, settings.SCREEN_HEIGHT - panel_h),
            (settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT),
            settings.EDU_PANEL_BG,
            -1,
        )
        cv2.addWeighted(overlay, settings.EDU_PANEL_ALPHA, frame, 1 - settings.EDU_PANEL_ALPHA, 0, frame)

        cv2.putText(
            frame,
            "MODO APRENDIZAJE IA",
            (24, settings.SCREEN_HEIGHT - 56),
            settings.FONT,
            0.9,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )
        cv2.putText(
            frame,
            text,
            (24, settings.SCREEN_HEIGHT - 18),
            settings.FONT,
            0.82,
            settings.EDU_TEXT_COLOR,
            2,
            cv2.LINE_AA,
        )

    # ---------- HUD mini (opcional) ----------
    def draw_hud(self, frame, telemetry):
        if telemetry is None:
            return
        overlay = frame.copy()
        pad = 18
        width = 360
        height = 150
        x0, y0 = pad, pad
        cv2.rectangle(overlay, (x0, y0), (x0 + width, y0 + height), settings.HUD_BG, -1)
        cv2.addWeighted(overlay, settings.HUD_ALPHA, frame, 1 - settings.HUD_ALPHA, 0, frame)

        rows = [
            ("vel_pelota", f"{telemetry.get('ball_speed', 0):.0f} px/s"),
            ("error_ia", f"{telemetry.get('p_miss', 0.0) * 100:.1f}%"),
            ("lat_ms", f"{telemetry.get('lat_ms', 0.0):.0f} ms"),
            ("decision", f"{telemetry.get('decision_hz', 0.0):.1f} Hz"),
        ]
        for i, (label, value) in enumerate(rows):
            y = y0 + 40 + i * 28
            cv2.putText(frame, label, (x0 + 16, y), settings.FONT, 0.6, settings.HUD_TEXT_COLOR, 1, cv2.LINE_AA)
            color = settings.HUD_VALUE_COLOR if i < 3 else settings.HUD_ALERT_COLOR
            cv2.putText(frame, value, (x0 + 180, y), settings.FONT, 0.7, color, 2, cv2.LINE_AA)

    # ---------- Cuenta regresiva de saque ----------
    def draw_countdown(self, frame, seconds_left):
        t = max(0.0, seconds_left)
        msg = f"{t:0.1f}s"
        cv2.putText(
            frame,
            msg,
            (int(settings.SCREEN_WIDTH * 0.47), int(settings.SCREEN_HEIGHT * 0.48)),
            settings.FONT,
            2.2,
            (255, 255, 255),
            5,
            cv2.LINE_AA,
        )