# main.py
# Hand Pong - Modo feria optimizado (ASCII)
# - Carga rapida (camara 640x360, MJPG, buffer corto)
# - Puntajes grandes y claros (la UI los dibuja a los lados)
# - Look Pong clasico: menu inicial, controles al pie, paletas/pelota blancas
# - Esqueleto H ON/OFF, pantalla completa G
# - Anillos de impacto ligeros

import cv2
import time
import numpy as np
import ctypes

import settings
from ai_strategy import OpponentModel
from hand_detector import HandDetector
from game_objects import PlayerPaddle, AIPaddle, Ball
from ui_manager import UIManager


# ---------------- Utilidades ventana/camara ----------------

def detect_display_resolution():
    """(Windows) Detecta resolucion de pantalla para fullscreen. Fallback a settings."""
    try:
        user32 = ctypes.windll.user32
        user32.SetProcessDPIAware()
        return int(user32.GetSystemMetrics(0)), int(user32.GetSystemMetrics(1))
    except Exception:
        return settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT

def fit_fill(frame, w, h):
    """Escala para llenar toda la ventana (puede recortar un poco)."""
    return cv2.resize(frame, (w, h), interpolation=cv2.INTER_LINEAR)

def fit_letterbox(frame, w, h):
    """Mantiene aspecto con barras (letterbox)."""
    H, W = frame.shape[:2]
    s = min(w / float(W), h / float(H))
    nw, nh = int(W * s), int(H * s)
    img = cv2.resize(frame, (nw, nh), interpolation=cv2.INTER_LINEAR)
    canvas = np.zeros((h, w, 3), dtype=np.uint8)
    x0, y0 = (w - nw) // 2, (h - nh) // 2
    canvas[y0:y0+nh, x0:x0+nw] = img
    return canvas


# ---------------- Efecto de anillos (ligero) ----------------

class HitRing:
    """Anillo de impacto: se expande y desvanece (implementacion ligera)."""
    __slots__ = ("x", "y", "age", "duration", "r0", "r1", "thick0")
    def __init__(self, x, y):
        self.x = int(x); self.y = int(y)
        self.age = 0.0
        self.duration = 0.35  # mas corto
        self.r0 = 6
        self.r1 = 90
        self.thick0 = 3

    def alive(self): 
        return self.age < self.duration

    def update(self, dt): 
        self.age += dt

    def draw(self, frame):
        t = max(0.0, min(1.0, self.age / self.duration))
        r = int(self.r0 + (self.r1 - self.r0) * t)
        thick = max(1, int(self.thick0 * (1.0 - t)))
        # color blanco con leve desvanecimiento (sin alpha real para ahorrar)
        col = (220 - int(160 * t),) * 3
        cv2.circle(frame, (self.x, self.y), r, col, thick, lineType=cv2.LINE_AA)


# ---------------- Aplicacion ----------------

class GameApp:
    def __init__(self):
        # 1) Resolucion y ventana
        if getattr(settings, "AUTO_FULLSCREEN", True):
            W, H = detect_display_resolution()
        else:
            W, H = settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT

        if hasattr(settings, "apply_resolution"):
            settings.apply_resolution(W, H)
        else:
            settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT = W, H

        cv2.namedWindow(settings.WINDOW_NAME, cv2.WINDOW_NORMAL)
        if getattr(settings, "AUTO_FULLSCREEN", True):
            cv2.setWindowProperty(settings.WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        else:
            cv2.resizeWindow(settings.WINDOW_NAME, settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT)

        # 2) Camara (config rapida)
        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # DSHOW acelera en Windows
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, settings.CAMERA_CAPTURE_W)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, settings.CAMERA_CAPTURE_H)
        self.cap.set(cv2.CAP_PROP_FPS, settings.CAMERA_FPS)
        try:
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # baja latencia
            fourcc = cv2.VideoWriter_fourcc(*"MJPG")
            self.cap.set(cv2.CAP_PROP_FOURCC, fourcc)
        except Exception:
            pass

        # 3) Sistemas
        self.ui = UIManager()
        self.detector = HandDetector()
        self.opponent = OpponentModel()

        # 4) Objetos de juego
        m = int(40 * (settings.SCREEN_HEIGHT / float(settings.BASE_HEIGHT)))
        self.player = PlayerPaddle(settings.SCREEN_WIDTH - settings.PADDLE_WIDTH - m, settings.PADDLE_R_COLOR)
        self.ai = AIPaddle(m, settings.PADDLE_L_COLOR)
        self.ball = Ball()

        # 5) Estado
        self.state = settings.MENU
        self.serve_dir = 1
        self.last_serve_time = 0.0
        self.score_player = 0
        self.score_ai = 0
        self.show_skeleton = True

        # 6) FX ligeros
        self.hit_rings = []

        # 7) Tiempos
        self._t_prev = time.time()

        print("ESPACIO: jugar/pausar | R: reiniciar | ESC: salir | H: esqueleto | G: pantalla completa")

    # ---------------- Bucle principal ----------------
    def run(self):
        while True:
            ok, frame = self.cap.read()
            if not ok:
                break

            t_now = time.time()
            dt = t_now - self._t_prev
            if dt > 0.05:  # limita paso para estabilidad y ahorro
                dt = 0.05
            elif dt < 0:
                dt = 0.0
            self._t_prev = t_now

            # Fondo camara
            frame = cv2.flip(frame, 1)
            if settings.CAMERA_FILL:
                frame = fit_fill(frame, settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT)
            else:
                frame = fit_letterbox(frame, settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT)

            # Mano y esqueleto (evitar sobrecoste si en MENU sin dibujo extra)
            y_norm, landmarks, _ = self.detector.process(frame)
            if self.show_skeleton and landmarks is not None:
                self.detector.draw_skeleton(frame, landmarks)

            # Estados
            if self.state == settings.MENU:
                self.ui.draw_menu(frame, subtitle="Pong con camara y mano")
                self._draw_objects(frame)  # que se vean paletas/bola en reposo

            elif self.state == settings.SERVE:
                remain = max(0.0, settings.SERVE_DELAY - (time.time() - self.last_serve_time))
                self.ui.draw_center_message(frame, "Listo", f"Comienza en {remain:.1f} s")
                self._draw_objects(frame)
                if remain <= 0.0:
                    self.state = settings.PLAYING

            elif self.state == settings.PLAYING:
                self.update_game(y_norm, dt)
                self._draw_objects(frame)

            elif self.state == settings.PAUSED:
                self.ui.draw_center_message(frame, "Pausa", "Presiona ESPACIO para continuar")
                self._draw_objects(frame)

            elif self.state == settings.GAME_OVER:
                self.ui.draw_center_message(frame, "Fin de la partida", "Presiona R para reiniciar")
                self._draw_objects(frame)

            # HUD (linea central + puntajes grandes + footer)
            self.ui.draw_center_line(frame)
            self.ui.draw_scores(frame, self.score_ai, self.score_player)
            self.ui.draw_footer_help(frame)

            # FX
            self._update_and_draw_rings(frame, dt)

            # Presentacion y teclas
            cv2.imshow(settings.WINDOW_NAME, frame)
            if self._handle_keys(cv2.waitKey(1) & 0xFF):
                break

        self.cap.release()
        cv2.destroyAllWindows()

    # ---------------- Entradas ----------------
    def _handle_keys(self, key):
        if key == 27:  # ESC
            return True

        elif key == ord(' '):  # ESPACIO
            if self.state in (settings.MENU, settings.GAME_OVER):
                self._reset_game()
                self.state = settings.SERVE
                self.last_serve_time = time.time()
            elif self.state == settings.PLAYING:
                self.state = settings.PAUSED
            elif self.state == settings.PAUSED:
                self.state = settings.PLAYING

        elif key == ord('r'):  # reiniciar
            self._reset_game()
            self.state = settings.SERVE
            self.last_serve_time = time.time()

        elif key == ord('h'):  # esqueleto ON/OFF
            self.show_skeleton = not self.show_skeleton

        elif key == ord('g'):  # pantalla completa toggle
            fs = cv2.getWindowProperty(settings.WINDOW_NAME, cv2.WND_PROP_FULLSCREEN)
            cv2.setWindowProperty(
                settings.WINDOW_NAME,
                cv2.WND_PROP_FULLSCREEN,
                cv2.WINDOW_NORMAL if fs == 1 else cv2.WINDOW_FULLSCREEN
            )

        return False

    # ---------------- Logica ----------------
    def _reset_game(self):
        self.score_player = 0
        self.score_ai = 0
        self.ball.reset(self.serve_dir)
        self.opponent = OpponentModel()
        self.hit_rings.clear()
        # Reinicia tiempo para progresion IA
        self._t_prev = time.time()

    def update_game(self, y_norm, dt):
        # Paleta del jugador via mano
        y_px = int(y_norm * settings.SCREEN_HEIGHT) if y_norm is not None else None
        self.player.update(y_px, dt)

        # IA hibrida (reactiva -> predictiva con tiempo)
        # Para ahorrar, usamos un tiempo de juego relativo a puntaje y transiciones.
        elapsed_min = 0.000001 + (self.score_ai + self.score_player) * 0.2  # crece por rondas (rapido y didactico)
        self.opponent.update(
            elapsed_min=elapsed_min,
            ball_y=self.ball.y,
            ball_dir=-1 if self.ball.vx < 0 else 1,
            paddle_y=self.ai.y,
            dt=dt,
            ball=self.ball,
            ai_paddle=self.ai,
            player_paddle=self.player
        )
        self.ai.update(self.opponent.last_target_y, dt)

        # Pelota
        self.ball.update(dt)

        # Colisiones -> anillos
        events = self.ball.check_collisions(self.ai, self.player)
        if events:
            for ev in events:
                if ev and ev[0] == "hit":
                    _, bx, by, _side, _power = ev
                    self.hit_rings.append(HitRing(bx, by))

        # Goles
        if self.ball.x < 0:
            self.score_player += 1
            self.opponent.on_point_end(player_scored=True, ball_final_y=self.ball.y)
            self.ball.reset(direction=-1)
            self.state = settings.SERVE
            self.last_serve_time = time.time()

        elif self.ball.x > settings.SCREEN_WIDTH:
            self.score_ai += 1
            self.opponent.on_point_end(player_scored=False, ball_final_y=self.ball.y)
            self.ball.reset(direction=1)
            self.state = settings.SERVE
            self.last_serve_time = time.time()

        # Fin de partida corta
        if max(self.score_player, self.score_ai) >= settings.WINNING_SCORE:
            self.state = settings.GAME_OVER

    # ---------------- Dibujo ----------------
    def _draw_objects(self, frame):
        # Paleta IA
        lx, ly, lw, lh = self.ai.rect()
        cv2.rectangle(frame, (lx, ly), (lx + lw, ly + lh), settings.PADDLE_L_COLOR, -1)
        # Paleta Jugador
        rx, ry, rw, rh = self.player.rect()
        cv2.rectangle(frame, (rx, ry), (rx + rw, ry + rh), settings.PADDLE_R_COLOR, -1)
        # Pelota
        cv2.circle(frame, (int(self.ball.x), int(self.ball.y)), settings.BALL_RADIUS, settings.BALL_COLOR, -1, lineType=cv2.LINE_AA)

    def _update_and_draw_rings(self, frame, dt):
        if not self.hit_rings:
            return
        # limpiar muertos
        alive = []
        for r in self.hit_rings:
            r.update(dt)
            if r.alive():
                r.draw(frame)
                alive.append(r)
        self.hit_rings = alive


if __name__ == "__main__":
    GameApp().run()