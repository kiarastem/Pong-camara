# Archivo: ui_manager.py - Interfaz educativa (marcador, panel, countdown)
# ASCII puro

import cv2
import time
import settings

class UIManager:
    def __init__(self):
        self.rings = []
        self.flash_color_val = None
        self.flash_alpha = 0.0

    def spawn_hit_ring(self, x, y):
        self.rings.append({"x": x, "y": y, "r": 10, "t": time.time()})

    def draw_rings(self, frame):
        now = time.time()
        new_rings = []
        for ring in self.rings:
            age = now - ring["t"]
            if age < 0.4:
                radius = int(ring["r"] + 200 * age)
                alpha = max(0.0, 1.0 - age / 0.4)
                color = (0, int(255 * alpha), 255)
                cv2.circle(frame, (int(ring["x"]), int(ring["y"])), radius, color, 2)
                new_rings.append(ring)
        self.rings = new_rings

    def flash_color(self, color):
        self.flash_color_val = color
        self.flash_alpha = 1.0

    def draw_flash(self, frame):
        if self.flash_color_val is None:
            return
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (frame.shape[1], frame.shape[0]), self.flash_color_val, -1)
        cv2.addWeighted(overlay, self.flash_alpha, frame, 1 - self.flash_alpha, 0, frame)
        self.flash_alpha -= 0.05
        if self.flash_alpha <= 0:
            self.flash_color_val = None

    def draw_score(self, frame, scores):
        text = f"{scores[0]}  |  {scores[1]}"
        cv2.putText(frame, text, (int(settings.SCREEN_WIDTH / 2 - 100), 80),
                    settings.FONT, settings.FONT_SCALE_SCORE, (255, 255, 255),
                    settings.FONT_THICKNESS_SCORE, cv2.LINE_AA)
        self.draw_rings(frame)
        self.draw_flash(frame)

    def draw_menu(self, frame, title, subtitle):
        cv2.putText(frame, title,
                    (int(settings.SCREEN_WIDTH / 2 - 220), int(settings.SCREEN_HEIGHT / 2 - 60)),
                    settings.FONT, 2, (255, 255, 255), 4, cv2.LINE_AA)
        cv2.putText(frame, subtitle,
                    (int(settings.SCREEN_WIDTH / 2 - 360), int(settings.SCREEN_HEIGHT / 2 + 20)),
                    settings.FONT, 1, (200, 200, 200), 2, cv2.LINE_AA)

    def draw_edu_panel(self, frame, text):
        panel_h = 90
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, settings.SCREEN_HEIGHT - panel_h),
                      (settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT),
                      settings.EDU_PANEL_BG, -1)
        cv2.addWeighted(overlay, settings.EDU_PANEL_ALPHA, frame, 1 - settings.EDU_PANEL_ALPHA, 0, frame)
        cv2.putText(frame, "MODO APRENDIZAJE IA",
                    (20, settings.SCREEN_HEIGHT - 55),
                    settings.FONT, 0.9, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, text,
                    (20, settings.SCREEN_HEIGHT - 20),
                    settings.FONT, 0.8, settings.EDU_TEXT_COLOR, 2, cv2.LINE_AA)

    def draw_countdown(self, frame, seconds_left):
        t = max(0.0, seconds_left)
        msg = f"{t:0.1f}s"
        cv2.putText(frame, msg,
                    (int(settings.SCREEN_WIDTH * 0.48), int(settings.SCREEN_HEIGHT * 0.45)),
                    settings.FONT, 2.2, (255, 255, 255), 5, cv2.LINE_AA)