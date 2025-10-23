# ui_manager.py
# Interfaz en espanol ASCII

import cv2
import time
import settings


class UIManager:
    def __init__(self):
        self.rings = []
        self.center_pulse_t0 = None
        self.center_pulse_color = (0, 255, 0)
        self.center_pulse_duration = 0.45
        self.paddle_pulse = {"left": None, "right": None}
        self.paddle_pulse_duration = 0.18
        self.wall_glows = []
        self.wall_glow_duration = 0.25

        self.edu_autoshow_seconds = 6.0
        self.edu_panel_alpha = 0.8
        self.edu_tips = [
            "La paleta IA comienza con baja precision y mejora poco a poco.",
            "Con el tiempo, la IA reacciona mas rapido y comete menos errores.",
            "La velocidad de la pelota aumenta de forma gradual.",
            "Tu controlas la paleta derecha con tu mano y la camara.",
            "Presiona H para mostrar u ocultar el esqueleto de la mano.",
        ]

    # ---------- elementos basicos ----------
    def draw_center_line(self, frame, dash_len=16, gap=14, thickness=2):
        x = frame.shape[1] // 2
        y = 0
        color = (255, 255, 255)
        h = frame.shape[0]
        while y < h:
            y2 = min(y + dash_len, h)
            cv2.line(frame, (x, y), (x, y2), color, thickness)
            y += dash_len + gap

    def draw_score(self, frame, scores):
        text = f"{scores[0]}    {scores[1]}"
        (tw, _), _ = cv2.getTextSize(text, settings.FONT, settings.FONT_SCALE_SCORE, settings.FONT_THICKNESS_SCORE)
        x = (frame.shape[1] - tw) // 2
        cv2.putText(frame, text, (x, 80), settings.FONT, settings.FONT_SCALE_SCORE,
                    (255, 255, 255), settings.FONT_THICKNESS_SCORE, cv2.LINE_AA)

    def draw_text_center(self, frame, text, y_offset=40, scale=1.0, color=(220, 220, 220)):
        (tw, _), _ = cv2.getTextSize(text, settings.FONT, scale, settings.FONT_THICKNESS_MSG)
        x = (frame.shape[1] - tw) // 2
        y = frame.shape[0] // 2 + y_offset
        cv2.putText(frame, text, (x, y), settings.FONT, scale, color, settings.FONT_THICKNESS_MSG, cv2.LINE_AA)

    # ---------- panel de controles ----------
    def draw_controls_panel(self, frame):
        lines = [
            "Controles",
            "  ESPACIO -> jugar / pausar",
            "  R       -> reiniciar",
            "  ESC     -> salir",
            "  H       -> mostrar esqueleto de la mano",
            "  G       -> pantalla completa",
            "  O       -> mostrar panel educativo",
            "  I       -> panel aprendizaje IA",
        ]
        pad_x, pad_y = 14, 12
        line_h = 22
        text_w = 0
        for s in lines:
            (tw, _), _ = cv2.getTextSize(s, settings.FONT, 0.7, 1)
            text_w = max(text_w, tw)
        panel_w = text_w + pad_x * 2
        panel_h = line_h * len(lines) + pad_y * 2
        x0 = frame.shape[1] - panel_w - 20
        y0 = 20

        overlay = frame.copy()
        cv2.rectangle(overlay, (x0, y0), (x0 + panel_w, y0 + panel_h), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.35, frame, 0.65, 0, frame)

        y = y0 + pad_y + 16
        for i, s in enumerate(lines):
            scale = 0.8 if i == 0 else 0.7
            thick = 2 if i == 0 else 1
            cv2.putText(frame, s, (x0 + pad_x, y), settings.FONT, scale, (235, 235, 235), thick, cv2.LINE_AA)
            y += line_h

    def draw_menu(self, frame, title, subtitle):
        (tw, _), _ = cv2.getTextSize(title, settings.FONT, 2, settings.FONT_THICKNESS_MSG)
        x_title = (frame.shape[1] - tw) // 2
        y_title = frame.shape[0] // 2 - 60
        cv2.putText(frame, title, (x_title, y_title), settings.FONT, 2, (255, 255, 255), 4, cv2.LINE_AA)

        (tw2, _), _ = cv2.getTextSize(subtitle, settings.FONT, 1, settings.FONT_THICKNESS_MSG)
        x_sub = (frame.shape[1] - tw2) // 2
        y_sub = frame.shape[0] // 2 + 20
        cv2.putText(frame, subtitle, (x_sub, y_sub), settings.FONT, 1, (200, 200, 200), 2, cv2.LINE_AA)

        self.draw_controls_panel(frame)

    # ---------- panel educativo ----------
    def draw_edu_panel(self, frame, alpha=0.8):
        pad_x, pad_y = 18, 16
        line_h = 24
        header = "Como aprende la IA"
        all_lines = [header] + self.edu_tips

        text_w = 0
        for s in all_lines:
            (tw, _), _ = cv2.getTextSize(s, settings.FONT, 0.8, 2)
            text_w = max(text_w, tw)

        panel_w = text_w + pad_x * 2
        panel_h = line_h * len(all_lines) + pad_y * 2

        W, H = frame.shape[1], frame.shape[0]
        x0 = (W - panel_w) // 2
        y0 = H - panel_h - 40

        overlay = frame.copy()
        cv2.rectangle(overlay, (x0, y0), (x0 + panel_w, y0 + panel_h), (0, 0, 0), -1)
        cv2.addWeighted(overlay, max(0.0, min(1.0, alpha)), frame, 1 - max(0.0, min(1.0, alpha)), 0, frame)

        y = y0 + pad_y + 6
        for i, s in enumerate(all_lines):
            scale = 0.9 if i == 0 else 0.8
            thick = 2 if i == 0 else 1
            color = (255, 255, 255) if i == 0 else (230, 230, 230)
            cv2.putText(frame, s, (x0 + pad_x, y), settings.FONT, scale, color, thick, cv2.LINE_AA)
            y += line_h

    def draw_edu_splash_auto(self, frame, menu_elapsed_sec, force_show=False):
        show = force_show or (menu_elapsed_sec <= self.edu_autoshow_seconds)
        if not show:
            return
        if force_show:
            alpha = self.edu_panel_alpha
        else:
            t = float(menu_elapsed_sec)
            edge = 0.8
            if t < edge:
                alpha = self.edu_panel_alpha * (t / edge)
            elif t > self.edu_autoshow_seconds - edge:
                alpha = self.edu_panel_alpha * ((self.edu_autoshow_seconds - t) / edge)
            else:
                alpha = self.edu_panel_alpha
        self.draw_edu_panel(frame, alpha=alpha)

    # ---------- panel de aprendizaje IA ----------
    def draw_ai_panel(self, frame, skill, react, max_spd, miss_prob):
        if not settings.AI_PANEL_ENABLED:
            return
        # panel en esquina superior izquierda
        pad_x, pad_y = 12, 10
        line_h = 22
        lines = [
            "IA - Aprendizaje",
            f"Progreso: {int(skill*100)}%",
            f"Reactividad: {react:.3f}",
            f"Velocidad max: {max_spd:.1f}",
            f"Prob error: {int(miss_prob*100)}%",
        ]

        # dimension texto
        text_w = 0
        for s in lines:
            (tw, _), _ = cv2.getTextSize(s, settings.FONT, 0.7, 1)
            text_w = max(text_w, tw)
        panel_w = text_w + pad_x * 2
        panel_h = line_h * len(lines) + pad_y * 2

        x0, y0 = 20, 20
        overlay = frame.copy()
        cv2.rectangle(overlay, (x0, y0), (x0 + panel_w, y0 + panel_h), settings.AI_PANEL_BG, -1)
        cv2.addWeighted(overlay, settings.AI_PANEL_ALPHA, frame, 1 - settings.AI_PANEL_ALPHA, 0, frame)

        y = y0 + pad_y + 16
        for i, s in enumerate(lines):
            color = settings.AI_PANEL_TEXT if i != 1 else settings.AI_PANEL_ACCENT
            thick = 2 if i == 0 else 1
            cv2.putText(frame, s, (x0 + pad_x, y), settings.FONT, 0.7, color, thick, cv2.LINE_AA)
            y += line_h

    # ---------- animaciones ----------
    def spawn_hit_ring(self, x, y, color=(255, 255, 255)):
        self.rings.append({"x": float(x), "y": float(y), "t": time.time(), "color": color})

    def draw_rings(self, frame):
        now = time.time()
        alive = []
        for r in self.rings:
            age = now - r["t"]
            if age <= 0.45:
                radius = int(14 + 220 * age)
                alpha = max(0.0, 1.0 - age / 0.45)
                color = tuple(int(c * alpha) for c in r["color"])
                cv2.circle(frame, (int(r["x"]), int(r["y"])), radius, color, 2, cv2.LINE_AA)
                alive.append(r)
        self.rings = alive

    def flash_center(self, color):
        self.center_pulse_t0 = time.time()
        self.center_pulse_color = tuple(int(c) for c in color)

    def draw_center_pulse(self, frame):
        if self.center_pulse_t0 is None:
            return
        age = time.time() - self.center_pulse_t0
        if age > self.center_pulse_duration:
            self.center_pulse_t0 = None
            return

        h, w = frame.shape[:2]
        cx, cy = w // 2, h // 2
        t = age / self.center_pulse_duration
        t_ease = 1.0 - (1.0 - t) * (1.0 - t)
        radius = int(min(w, h) * 0.6 * t_ease + 12)
        alpha = max(0.0, 0.55 * (1.0 - t_ease))

        overlay = frame.copy()
        cv2.circle(overlay, (cx, cy), radius, self.center_pulse_color, -1, cv2.LINE_AA)
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

    def pulse_paddle(self, side):
        side = "left" if side == "left" else "right"
        self.paddle_pulse[side] = time.time()

    def draw_paddle_pulse(self, frame, paddle_rect, side):
        t0 = self.paddle_pulse.get(side)
        if t0 is None:
            return
        age = time.time() - t0
        if age > self.paddle_pulse_duration:
            self.paddle_pulse[side] = None
            return

        t = age / self.paddle_pulse_duration
        thickness = max(1, int(6 * (1.0 - t) + 1))

        x, y, w, h = paddle_rect
        pad = int(4 + 10 * (1.0 - t))
        x0, y0 = x - pad, y - pad
        x1, y1 = x + w + pad, y + h + pad

        color = (200, 255, 255) if side == "right" else (180, 255, 200)
        cv2.rectangle(frame, (x0, y0), (x1, y1), color, thickness, cv2.LINE_AA)

    def spawn_wall_glow(self, x, y):
        side = "top" if y <= 10 else "bottom"
        self.wall_glows.append({"x": float(x), "y": float(y), "t": time.time(), "side": side})

    def draw_wall_glows(self, frame):
        now = time.time()
        alive = []
        for g in self.wall_glows:
            age = now - g["t"]
            if age <= self.wall_glow_duration:
                t = age / self.wall_glow_duration
                alpha = max(0.0, 0.65 * (1.0 - t))
                h, w = frame.shape[:2]
                y = 6 if g["side"] == "top" else h - 6
                overlay = frame.copy()
                span = int(120 + 200 * (1.0 - t))
                x0 = int(max(0, g["x"] - span))
                x1 = int(min(w - 1, g["x"] + span))
                cv2.rectangle(overlay, (x0, y - 6), (x1, y + 6), (255, 255, 255), -1)
                cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
                alive.append(g)
        self.wall_glows = alive

    def draw_serve_ready(self, frame, t_frac):
        t = max(0.0, min(1.0, float(t_frac)))
        h, w = frame.shape[:2]
        cx, cy = w // 2, h // 2
        radius = int(24 + t * (min(w, h) * 0.35))
        color = (255, 255, 255)
        cv2.circle(frame, (cx, cy), radius, color, 2, cv2.LINE_AA)
        self.draw_text_center(frame, "LISTO", y_offset=0, scale=1.2, color=(240, 240, 240))
