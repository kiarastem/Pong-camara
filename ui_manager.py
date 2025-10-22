# Archivo: ui_manager.py - Interfaz educativa (marcador, panel, countdown, HUD)
# ASCII puro

import time
import cv2
import settings


class UIManager:
    def __init__(self):
        self.rings = []
        self.flash_color_val = None
        self.flash_alpha = 0.0

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
            color = (0, int(200 * alpha), 255)
            cv2.circle(frame, (int(ring["x"]), int(ring["y"])), radius, color, 2)
            survivors.append(ring)
        self.rings = survivors

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

    def draw_score(self, frame, scores):
        text = f"{scores[0]}  |  {scores[1]}"
        cv2.putText(
            frame,
            text,
            (int(settings.SCREEN_WIDTH / 2 - 110), 100),
            settings.FONT,
            settings.FONT_SCALE_SCORE,
            (255, 255, 255),
            settings.FONT_THICKNESS_SCORE,
            cv2.LINE_AA,
        )
        self._draw_rings(frame)
        self._draw_flash(frame)

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

    def draw_hud(self, frame, telemetry, tuning):
        if not settings.HUD_VISIBLE or telemetry is None:
            return
        overlay = frame.copy()
        pad = 18
        width = 420
        height = 210
        x0, y0 = pad, pad
        cv2.rectangle(overlay, (x0, y0), (x0 + width, y0 + height), settings.HUD_BG, -1)
        cv2.addWeighted(overlay, settings.HUD_ALPHA, frame, 1 - settings.HUD_ALPHA, 0, frame)

        rows = [
            ("Ball speed", f"{telemetry.get('ball_speed', 0):.0f} px/s"),
            ("AI miss", f"{telemetry.get('p_miss', 0.0) * 100:.1f}%"),
            ("Latency", f"{telemetry.get('lat_ms', 0.0):.0f} ms"),
            ("Decision", f"{telemetry.get('decision_hz', 0.0):.1f} Hz"),
        ]
        for i, (label, value) in enumerate(rows):
            y = y0 + 36 + i * 26
            cv2.putText(frame, label, (x0 + 16, y), settings.FONT, 0.63, settings.HUD_TEXT_COLOR, 1, cv2.LINE_AA)
            color = settings.HUD_VALUE_COLOR if i < 3 else settings.HUD_ALERT_COLOR
            cv2.putText(frame, value, (x0 + 210, y), settings.FONT, 0.73, color, 2, cv2.LINE_AA)

        # tuning visible
        ty = y0 + 36 + len(rows) * 26 + 12
        cv2.putText(frame, "Tuning:", (x0 + 16, ty), settings.FONT, 0.63, (220, 230, 255), 1, cv2.LINE_AA)
        ty += 26
        trows = [
            (f"AI_MAX_SPEED", f"{tuning['AI_PADDLE_MAX_SPEED']:.0f}"),
            (f"AI_D_GAIN", f"{tuning['AI_D_GAIN']:.2f}"),
            (f"AI_DEADBAND_PX", f"{tuning['AI_DEADBAND_PX']:.0f}"),
            (f"AI_MAX_ACCEL", f"{tuning['AI_MAX_ACCEL']:.0f}"),
        ]
        for k, v in trows:
            cv2.putText(frame, f"{k}", (x0 + 16, ty), settings.FONT, 0.6, (200, 210, 240), 1, cv2.LINE_AA)
            cv2.putText(frame, f"{v}", (x0 + 210, ty), settings.FONT, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
            ty += 24

    def draw_ticker(self, frame, text):
        if not text:
            return
        bar_h = 44
        overlay = frame.copy()
        cv2.rectangle(
            overlay,
            (0, settings.SCREEN_HEIGHT - bar_h),
            (settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT),
            (10, 18, 26),
            -1,
        )
        cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)
        cv2.putText(
            frame,
            text,
            (30, settings.SCREEN_HEIGHT - 14),
            settings.FONT,
            0.72,
            (220, 240, 255),
            2,
            cv2.LINE_AA,
        )