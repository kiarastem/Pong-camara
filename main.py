# main.py
# Hand Pong — versión educativa con menú, panel y cámara visible

import cv2
import time
import numpy as np
import ctypes

import settings
from ai_strategy import OpponentModel
from hand_detector import HandDetector
from game_objects import PlayerPaddle, AIPaddle, Ball
from ui_manager import UIManager


def detect_display_resolution():
    try:
        user32 = ctypes.windll.user32
        user32.SetProcessDPIAware()
        return int(user32.GetSystemMetrics(0)), int(user32.GetSystemMetrics(1))
    except Exception:
        return settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT


def fit_fill(frame, w, h):
    return cv2.resize(frame, (w, h), interpolation=cv2.INTER_LINEAR)


def fit_letterbox(frame, w, h):
    H, W = frame.shape[:2]
    s = min(w / float(W), h / float(H))
    nw, nh = int(W * s), int(H * s)
    img = cv2.resize(frame, (nw, nh), interpolation=cv2.INTER_LINEAR)
    canvas = np.zeros((h, w, 3), dtype=np.uint8)
    x0, y0 = (w - nw) // 2, (h - nh) // 2
    canvas[y0:y0+nh, x0:x0+nw] = img
    return canvas


class HitRing:
    def __init__(self, x, y):
        self.x, self.y = int(x), int(y)
        self.age = 0.0
        self.duration = 0.35
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
        col = (220 - int(160 * t),) * 3
        cv2.circle(frame, (self.x, self.y), r, col, thick, lineType=cv2.LINE_AA)


class GameApp:
    def __init__(self):
        W, H = detect_display_resolution() if settings.AUTO_FULLSCREEN else (settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT)
        settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT = W, H

        cv2.namedWindow(settings.WINDOW_NAME, cv2.WINDOW_NORMAL)
        if settings.AUTO_FULLSCREEN:
            cv2.setWindowProperty(settings.WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        else:
            cv2.resizeWindow(settings.WINDOW_NAME, W, H)

        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, settings.CAMERA_CAPTURE_W)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, settings.CAMERA_CAPTURE_H)
        self.cap.set(cv2.CAP_PROP_FPS, settings.CAMERA_FPS)
        try:
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
        except Exception:
            pass

        self.ui = UIManager()
        self.detector = HandDetector()
        self.opponent = OpponentModel()
        self.player = PlayerPaddle(W - settings.PADDLE_WIDTH - 40, settings.PADDLE_R_COLOR)
        self.ai = AIPaddle(40, settings.PADDLE_L_COLOR)
        self.ball = Ball()

        self.state = settings.MENU
        self.serve_dir = 1
        self.last_serve_time = 0.0
        self.score_player = 0
        self.score_ai = 0
        self.show_skeleton = True
        self.show_edu_panel = False
        self.hit_rings = []
        self._t_prev = time.time()

        print("ESPACIO: jugar/pausar | R: reiniciar | ESC: salir | H: esqueleto | G: pantalla completa | O: panel educativo")

    def run(self):
        while True:
            ok, frame = self.cap.read()
            if not ok:
                break

            t_now = time.time()
            dt = max(0.0, min(0.05, t_now - self._t_prev))
            self._t_prev = t_now

            frame = cv2.flip(frame, 1)
            frame = fit_fill(frame, settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT)

            y_norm, lm, _ = self.detector.process(frame)
            if self.show_skeleton and lm is not None:
                self.detector.draw_skeleton(frame, lm)

            if self.state == settings.MENU:
                self.ui.draw_menu(frame, subtitle="Pong controlado por cámara")
                self._draw_objects(frame)
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
                self.ui.draw_center_message(frame, "Fin del juego", "Presiona R para reiniciar")
                self._draw_objects(frame)

            self.ui.draw_center_line(frame)
            self.ui.draw_scores(frame, self.score_ai, self.score_player)
            self.ui.draw_footer_help(frame)

            if self.state == settings.PLAYING:
                if self.opponent.adv_pred_y is not None:
                    self.ui.draw_prediction_line(frame, (self.ball.x, self.ball.y), self.opponent.adv_pred_y, self.ai.x + self.ai.width)
                if self.show_edu_panel:
                    self.ui.draw_edu_panel(frame, {
                        "error_rate": self.opponent.err_rate,
                        "mix": self.opponent.mix,
                        "adv_pred_y": self.opponent.adv_pred_y,
                        "ball_y": self.ball.y
                    })

            self._update_and_draw_rings(frame, dt)
            cv2.imshow(settings.WINDOW_NAME, frame)
            if self._handle_keys(cv2.waitKey(1) & 0xFF):
                break

        self.cap.release()
        cv2.destroyAllWindows()

    def _handle_keys(self, key):
        if key == 27:
            return True
        elif key == ord(' '):
            if self.state in (settings.MENU, settings.GAME_OVER):
                self._reset_game()
                self.state = settings.SERVE
                self.last_serve_time = time.time()
            elif self.state == settings.PLAYING:
                self.state = settings.PAUSED
            elif self.state == settings.PAUSED:
                self.state = settings.PLAYING
        elif key == ord('r'):
            self._reset_game()
            self.state = settings.SERVE
            self.last_serve_time = time.time()
        elif key == ord('h'):
            self.show_skeleton = not self.show_skeleton
        elif key == ord('g'):
            fs = cv2.getWindowProperty(settings.WINDOW_NAME, cv2.WND_PROP_FULLSCREEN)
            cv2.setWindowProperty(settings.WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL if fs == 1 else cv2.WINDOW_FULLSCREEN)
        elif key == ord('o'):
            self.show_edu_panel = not self.show_edu_panel
        return False

    def _reset_game(self):
        self.score_player = 0
        self.score_ai = 0
        self.ball.reset(self.serve_dir)
        self.opponent = OpponentModel()
        self.hit_rings.clear()

    def update_game(self, y_norm, dt):
        y_px = int(y_norm * settings.SCREEN_HEIGHT) if y_norm is not None else None
        self.player.update(y_px, dt)

        elapsed_min = 0.000001 + (self.score_ai + self.score_player) * 0.2
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
        self.ball.update(dt)

        events = self.ball.check_collisions(self.ai, self.player)
        for ev in events or []:
            if ev and ev[0] == "hit":
                _, bx, by, _side, _power = ev
                self.hit_rings.append(HitRing(bx, by))

        if self.ball.x < 0:
            self.score_player += 1
            self.ball.reset(direction=-1)
            self.state = settings.SERVE
            self.last_serve_time = time.time()
        elif self.ball.x > settings.SCREEN_WIDTH:
            self.score_ai += 1
            self.ball.reset(direction=1)
            self.state = settings.SERVE
            self.last_serve_time = time.time()

        if max(self.score_player, self.score_ai) >= settings.WINNING_SCORE:
            self.state = settings.GAME_OVER

    def _draw_objects(self, frame):
        cv2.rectangle(frame, (self.ai.x, self.ai.y), (self.ai.x + self.ai.width, self.ai.y + self.ai.height), settings.PADDLE_L_COLOR, -1)
        cv2.rectangle(frame, (self.player.x, self.player.y), (self.player.x + self.player.width, self.player.y + self.player.height), settings.PADDLE_R_COLOR, -1)
        cv2.circle(frame, (int(self.ball.x), int(self.ball.y)), settings.BALL_RADIUS, settings.BALL_COLOR, -1, lineType=cv2.LINE_AA)

    def _update_and_draw_rings(self, frame, dt):
        alive = []
        for r in self.hit_rings:
            r.update(dt)
            if r.alive():
                r.draw(frame)
                alive.append(r)
        self.hit_rings = alive


if __name__ == "__main__":
    GameApp().run()