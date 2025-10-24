# main.py - Hand Pong en espanol ASCII con EMA de mano, menu de perfiles y panel opcional

import cv2
import time
import math
import numpy as np

import settings
from hand_detector import HandDetector
from game_objects import PlayerPaddle, AIPaddle, Ball
from ai_strategy import OpponentAI

# ---------- util ----------
def fit_fill(frame, w, h):
    return cv2.resize(frame, (w, h), interpolation=cv2.INTER_LINEAR)

def draw_text(frame, txt, x, y, scale, color, thickness=2, center=False):
    font = cv2.FONT_HERSHEY_SIMPLEX
    (tw, th), _ = cv2.getTextSize(txt, font, scale, thickness)
    if center:
        x = int(x - tw / 2)
    cv2.putText(frame, txt, (int(x), int(y)), font, scale, color, thickness, cv2.LINE_AA)

def clamp(v, a, b):
    return max(a, min(b, v))

# ---------- app ----------
class GameApp:
    def __init__(self):
        self.w = settings.SCREEN_WIDTH
        self.h = settings.SCREEN_HEIGHT

        cv2.namedWindow(settings.WINDOW_NAME, cv2.WINDOW_NORMAL)
        if settings.FULLSCREEN:
            cv2.setWindowProperty(settings.WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        else:
            cv2.resizeWindow(settings.WINDOW_NAME, self.w, self.h)
        self.window_name = settings.WINDOW_NAME

        # Estados
        self.state = "MENU"  # MENU -> SERVE -> PLAYING -> PAUSED/GAME_OVER
        self.last_serve = time.time()
        self.score_p = 0
        self.score_ai = 0

        # Objetos
        margin = 40
        self.player = PlayerPaddle(self.w - settings.PADDLE_WIDTH - margin, settings.PADDLE_R_COLOR)
        self.ai     = AIPaddle(margin, settings.PADDLE_L_COLOR)
        self.ball   = Ball()

        # IA
        self.ai_brain = OpponentAI(self.ai.x)

        # Entrada
        self.detector = HandDetector()
        self.input_safe = not getattr(self.detector, "enabled", False)
        self.y_from_mouse = self.h // 2
        self.key_up = False
        self.key_down = False
        cv2.setMouseCallback(self.window_name, self._on_mouse)

        # Suavizado de mano/mouse (EMA)
        self.hand_y_ema = self.h // 2

        # Camara
        self.cap = cv2.VideoCapture(settings.CAMERA_INDEX, cv2.CAP_DSHOW)
        self.cam_ok = self.cap.isOpened()
        if self.cam_ok:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, settings.CAMERA_CAPTURE_W)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, settings.CAMERA_CAPTURE_H)
            self.cap.set(cv2.CAP_PROP_FPS, settings.CAMERA_FPS)
            try:
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
            except Exception:
                pass

        # Visuales
        self.show_skeleton = True
        self.show_panel = settings.EDU_PANEL_ENABLED  # empieza como diga settings (False por defecto)

        # Telemetria
        self.last_speed = 0.0
        self.last_angle_deg = 0.0

        # Tiempo
        self.t_prev = time.time()

        print("Controles: ESPACIO iniciar/pausar/continuar | R reiniciar | ESC salir | H esqueleto | E panel | 1/2/3 perfil")

    # -------- bucle --------
    def run(self):
        while True:
            frame = self._grab_frame()

            # dt
            t = time.time()
            dt = max(0.0, min(0.05, t - self.t_prev))
            self.t_prev = t

            # Mano (si disponible y no en menu)
            y_norm = None
            landmarks = None
            valid = False
            if not self.input_safe and self.state != "MENU":
                y_norm, landmarks, valid = self.detector.process(frame)
                if self.show_skeleton and landmarks is not None:
                    self.detector.draw_skeleton(frame, landmarks)

            # Respaldo (mouse/teclas) fuera del menu
            if self.state != "MENU" and (self.input_safe or not valid or y_norm is None):
                y_px = int(self.y_from_mouse)
                if self.key_up:   y_px -= int(900 * dt)
                if self.key_down: y_px += int(900 * dt)

                # margen seguro para el centro de la paleta
                margin = settings.PADDLE_HEIGHT // 2 + 6
                y_px = clamp(y_px, margin, self.h - margin)

                # EMA para que no rebote
                alpha = float(getattr(settings, "HAND_EMA_ALPHA", 0.28))
                self.hand_y_ema = int((1.0 - alpha) * self.hand_y_ema + alpha * y_px)

                y_norm = self.hand_y_ema / max(1, self.h)
                self._draw_banner(frame, "Entrada alterna: MOUSE o FLECHAS", (60, 210, 255))

            # Estados
            if self.state == "MENU":
                self._draw_menu(frame)
            elif self.state == "SERVE":
                remain = max(0.0, settings.SERVE_DELAY - (time.time() - self.last_serve))
                self._draw_center(frame, "Listo", 0.9)
                self._draw_center(frame, f"Saque en {remain:.1f} s", 0.6, dy=60)
                if remain <= 0.0:
                    self.state = "PLAYING"
            elif self.state == "PLAYING":
                self._update_game(y_norm, dt)
            elif self.state == "PAUSED":
                self._draw_center(frame, "Pausa", 0.9)
                self._draw_center(frame, "Pulsa ESPACIO para continuar", 0.6, dy=60)
            elif self.state == "GAME_OVER":
                msg = "Ganaste" if self.score_p > self.score_ai else "Perdiste"
                self._draw_center(frame, "Fin del juego", 0.9)
                self._draw_center(frame, msg, 0.7, dy=60)
                self._draw_center(frame, "Pulsa ESPACIO para jugar de nuevo", 0.6, dy=110)

            # Dibujo comun
            if self.state != "MENU":
                # IA mas lenta/rapida segun skill (anti-tiriteo se maneja en ai_strategy)
                self.ai.max_speed = int(settings.PADDLE_MAX_SPEED * (0.6 + 0.4 * self.ai_brain.skill))

                self._draw_gameplay(frame)
                self._draw_center_line(frame)
                self._draw_score(frame)
                self._draw_footer(frame)

                if self.state == "PLAYING" and self.show_panel:
                    self._draw_edu_panel(frame)

                if self.state == "PLAYING" and settings.SHOW_PREDICTION and self.ai_brain.pred_y is not None:
                    x_line = self.ai.x + self.ai.width
                    cv2.circle(frame, (x_line, int(self.ai_brain.pred_y)), 6, settings.PRED_LINE_COLOR, 2, cv2.LINE_AA)

            cv2.imshow(self.window_name, frame)
            if self._handle_keys(cv2.waitKey(1) & 0xFF):
                break

        if self.cam_ok:
            self.cap.release()
        cv2.destroyAllWindows()

    # -------- logica --------
    def _update_game(self, y_norm, dt):
        # Jugador (mano con EMA y margen)
        if y_norm is not None:
            margin = settings.PADDLE_HEIGHT // 2 + 6
            raw_y = int(y_norm * self.h)
            raw_y = clamp(raw_y, margin, self.h - margin)
            alpha = float(getattr(settings, "HAND_EMA_ALPHA", 0.28))
            self.hand_y_ema = int((1.0 - alpha) * self.hand_y_ema + alpha * raw_y)
            y_px = self.hand_y_ema
        else:
            y_px = None

        self.player.update(y_px, dt)

        # IA
        ai_target = self.ai_brain.decide(self.ball, self.ai.center_y(), dt)
        self.ai.update(int(ai_target), dt)

        # Pelota
        self.ball.update(dt)

        # Telemetria
        vx = float(getattr(self.ball, "vx", 0.0))
        vy = float(getattr(self.ball, "vy", 0.0))
        self.last_speed = math.hypot(vx, vy)
        self.last_angle_deg = math.degrees(math.atan2(vy, vx if abs(vx) > 1e-6 else 1e-6))

        # Colisiones
        _ = self.ball.check_collisions(self.ai, self.player)

        # Goles
        if self.ball.x < 0:
            self.score_p += 1
            self.ai_brain.learn_on_point_end(player_scored=True, ball_final_y=float(self.ball.y))
            self.ball.reset(direction=-1)
            self.state = "SERVE"
            self.last_serve = time.time()
        elif self.ball.x > self.w:
            self.score_ai += 1
            self.ai_brain.learn_on_point_end(player_scored=False, ball_final_y=float(self.ball.y))
            self.ball.reset(direction=1)
            self.state = "SERVE"
            self.last_serve = time.time()

        if max(self.score_p, self.score_ai) >= settings.WINNING_SCORE:
            self.state = "GAME_OVER"

    # -------- entrada --------
    def _handle_keys(self, key):
        if key == 27:  # ESC
            return True

        # cambiar perfil en cualquier estado
        if key in (ord('1'), ord('2'), ord('3')):
            settings.BALL_PROFILE = int(chr(key))
            # actualizar limites de la pelota al vuelo
            self.ball.apply_profile_change()
            print("Perfil activo:", settings.BALL_PROFILES[settings.BALL_PROFILE]["name"])

        # ESPACIO maneja flujo
        if key == ord(' '):
            if self.state == "MENU":
                self._reset_match()
                self.state = "SERVE"
                self.last_serve = time.time()
            elif self.state == "SERVE":
                self.state = "PLAYING"
            elif self.state == "PLAYING":
                self.state = "PAUSED"
            elif self.state == "PAUSED":
                self.state = "PLAYING"
            elif self.state == "GAME_OVER":
                self._reset_match()
                self.state = "SERVE"
                self.last_serve = time.time()

        elif key == ord('r'):
            self._reset_match()
            self.state = "SERVE"
            self.last_serve = time.time()
        elif key == ord('h'):
            self.show_skeleton = not self.show_skeleton
        elif key == ord('e'):
            self.show_panel = not self.show_panel

        # Flechas / WASD (fuera de menu)
        if self.state != "MENU":
            if key in (82, ord('w')):
                self.key_up, self.key_down = True, False
            elif key in (84, ord('s')):
                self.key_up, self.key_down = False, True
            elif key == 255:
                pass
            else:
                self.key_up = self.key_down = False

        return False

    def _on_mouse(self, event, x, y, flags, param):
        if event in (cv2.EVENT_MOUSEMOVE, cv2.EVENT_LBUTTONDOWN, cv2.EVENT_LBUTTONUP):
            self.y_from_mouse = y

    # -------- frame/camara --------
    def _grab_frame(self):
        if self.cam_ok:
            ok, frame = self.cap.read()
            if not ok:
                self.cam_ok = False
                return np.full((self.h, self.w, 3), 25, dtype=np.uint8)
            frame = cv2.flip(frame, 1)
            return fit_fill(frame, self.w, self.h)
        else:
            color = 15 if self.state == "MENU" else 25
            return np.full((self.h, self.w, 3), color, dtype=np.uint8)

    # -------- dibujo --------
    def _draw_menu(self, frame):
        nombre = settings.BALL_PROFILES[settings.BALL_PROFILE]["name"]
        self._draw_center(frame, "Hand Pong", 1.1, dy=-60)
        draw_text(frame, "Pulsa ESPACIO para iniciar", self.w // 2, int(self.h * 0.55), 0.7, (255, 255, 255), 2, center=True)
        draw_text(frame, "Controles: mano (si hay camara) o MOUSE / FLECHAS", self.w // 2, int(self.h * 0.64), 0.55, (230, 230, 230), 2, center=True)
        draw_text(frame, "Velocidad: 1=Lento  2=Normal  3=Rapido", self.w // 2, int(self.h * 0.73), 0.6, (210, 210, 210), 2, center=True)
        draw_text(frame, f"Perfil actual: {nombre}", self.w // 2, int(self.h * 0.80), 0.65, (255, 255, 255), 2, center=True)
        draw_text(frame, "E: panel  |  H: esqueleto  |  R: reiniciar  |  ESC: salir", self.w // 2, int(self.h * 0.88), 0.5, (210, 210, 210), 2, center=True)

    def _draw_center(self, frame, text, scale=1.0, dy=0, color=(255, 255, 255)):
        draw_text(frame, text, self.w // 2, self.h // 2 + dy, scale, color, thickness=2, center=True)

    def _draw_center_line(self, frame):
        for y in range(0, self.h, 24):
            cv2.line(frame, (self.w // 2, y), (self.w // 2, y + 12), (255, 255, 255), 2, cv2.LINE_AA)

    def _draw_score(self, frame):
        s = f"{self.score_ai}   {self.score_p}"
        draw_text(frame, s, self.w // 2, 60, 1.6, (255, 255, 255), thickness=3, center=True)

    def _draw_footer(self, frame):
        nombre = settings.BALL_PROFILES[settings.BALL_PROFILE]["name"]
        footer = f"ESPACIO: iniciar/pausar | R: reiniciar | ESC: salir | H: esqueleto | E: panel | Perfil: {nombre} (1/2/3)"
        draw_text(frame, footer, 20, self.h - 20, 0.7, (235, 235, 235), thickness=2, center=False)

    def _draw_gameplay(self, frame):
        cv2.rectangle(frame, (self.ai.x, self.ai.y),
                      (self.ai.x + self.ai.width, self.ai.y + self.ai.height),
                      settings.PADDLE_L_COLOR, -1)
        cv2.rectangle(frame, (self.player.x, self.player.y),
                      (self.player.x + self.player.width, self.player.y + self.player.height),
                      settings.PADDLE_R_COLOR, -1)
        cv2.circle(frame, (int(self.ball.x), int(self.ball.y)), settings.BALL_RADIUS, settings.BALL_COLOR, -1, cv2.LINE_AA)

    def _draw_banner(self, frame, text, color=(60, 210, 255)):
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (self.w, 40), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.55, frame, 0.45, 0, frame)
        draw_text(frame, text, 16, 28, 0.6, color, 2, center=False)

    def _draw_edu_panel(self, frame):
        # Panel reducido: Prediccion, Exactitud, Error IA, Aprendizaje
        pad = settings.EDU_PANEL_PADDING
        w_panel = int(self.w * settings.EDU_PANEL_WIDTH_FRAC)
        x0 = self.w - w_panel - pad
        y0 = pad
        x1 = self.w - pad
        y1 = int(self.h * 0.40)

        overlay = frame.copy()
        cv2.rectangle(overlay, (x0, y0), (x1, y1), (0, 0, 0), -1)
        cv2.addWeighted(overlay, settings.EDU_PANEL_ALPHA, frame, 1 - settings.EDU_PANEL_ALPHA, 0, frame)

        sx = x0 + 16
        sy = y0 + 28
        lh = 26
        scale = settings.EDU_TEXT_SCALE
        thick = settings.EDU_TEXT_THICK

        draw_text(frame, "Panel educativo", sx, sy, scale + 0.05, (255, 255, 255), thick); sy += lh * 2

        pred_txt = "n/a" if self.ai_brain.pred_y is None else f"{int(self.ai_brain.pred_y)} px"
        draw_text(frame, f"Prediccion: {pred_txt}", sx, sy, scale, (200, 255, 200), thick); sy += lh
        draw_text(frame, f"Exactitud: {self.ai_brain.acc_recent:4.1f} %", sx, sy, scale, (255, 230, 150), thick); sy += lh
        draw_text(frame, f"Error IA: {self.ai_brain.error_pct:4.1f} %", sx, sy, scale, (255, 180, 180), thick); sy += lh
        draw_text(frame, f"Aprendizaje: {int(self.ai_brain.skill*100):3d} %", sx, sy, scale, (200, 220, 255), thick); sy += lh

    def _reset_match(self):
        self.score_p = 0
        self.score_ai = 0
        self.ball.reset(direction=1)

if __name__ == "__main__":
    GameApp().run()