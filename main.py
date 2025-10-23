# main.py
# Bucle principal del juego: camara, deteccion de mano, estados y render.
# Espanol sin tildes (ASCII)

import os, warnings
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
warnings.filterwarnings("ignore")

import cv2
import time

from game_objects import PlayerPaddle, AIPaddle, Ball
from hand_detector import HandDetector
from ui_manager import UIManager
import settings


def fast_blur_bgr(frame, scale=0.4, ksize=9):
    small = cv2.resize(frame, (0, 0), fx=scale, fy=scale)
    small = cv2.GaussianBlur(small, (ksize | 1, ksize | 1), 0)
    return cv2.resize(small, (frame.shape[1], frame.shape[0]))


class GameApp:
    def __init__(self, camera_index=0):
        # camara
        self.cap = cv2.VideoCapture(camera_index)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, settings.SCREEN_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, settings.SCREEN_HEIGHT)

        # sistemas
        self.detector = HandDetector()
        self.ui = UIManager()

        # objetos
        margin = 40
        self.player = PlayerPaddle(settings.SCREEN_WIDTH - settings.PADDLE_WIDTH - margin, settings.PADDLE_R_COLOR)
        self.ai = AIPaddle(margin, settings.PADDLE_L_COLOR)
        self.ball = Ball()

        # estado
        self.state = settings.MENU
        self.scores = [0, 0]
        self.start_time = time.time()
        self.serve_time = None
        self.serve_dir = 1

        # UI toggles
        self.show_skeleton = bool(settings.SHOW_HAND_SKELETON)
        self.force_info_panel = False  # O
        self.show_ai_panel = True      # I
        self.menu_time_start = time.time()

        # feedback de mano
        self.no_hand_frames = 0
        self.no_hand_hint_after = 20

        # ventana
        self.window_title = settings.WINDOW_NAME
        cv2.namedWindow(self.window_title, cv2.WINDOW_NORMAL)
        if getattr(settings, "FULLSCREEN", False):
            cv2.setWindowProperty(self.window_title, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        else:
            cv2.resizeWindow(self.window_title, settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT)

        print("ESPACIO: jugar/pausar | R: reiniciar | ESC: salir | H: esqueleto | G: pantalla completa | O: panel educativo | I: panel IA")

    def toggle_fullscreen(self):
        fs = cv2.getWindowProperty(self.window_title, cv2.WND_PROP_FULLSCREEN)
        if fs < 1:
            cv2.setWindowProperty(self.window_title, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        else:
            cv2.setWindowProperty(self.window_title, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(self.window_title, settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT)

    def reset_game(self):
        self.scores = [0, 0]
        self.ball.reset(direction=self.serve_dir)
        self.start_time = time.time()
        self.state = settings.MENU
        self.serve_time = None
        self.menu_time_start = time.time()
        self.no_hand_frames = 0

    def start_serve(self, direction):
        self.ball.reset(direction=direction, randomize_angle=True)
        self.serve_time = time.time()
        self.state = settings.SERVE
        self.no_hand_frames = 0

    def toggle_pause(self):
        if self.state == settings.PLAYING:
            self.state = settings.PAUSED
        elif self.state in (settings.PAUSED, settings.MENU, settings.SERVE):
            self.state = settings.PLAYING

    # progresion de IA (devuelve ademas el progreso 0..1)
    def _ai_progress_params(self):
        elapsed_min = max(0.0, (time.time() - self.start_time) / 60.0)
        progress = min(1.0, (elapsed_min / max(0.001, settings.AI_RAMP_MINUTES)) ** settings.AI_TIME_EXP)
        ai_react = settings.INITIAL_AI_REACTIVITY + settings.AI_REACTIVITY_PER_MIN * (elapsed_min ** settings.AI_TIME_EXP)
        speed_boost = settings.AI_MAX_SPEED_START + (settings.AI_MAX_SPEED_END - settings.AI_MAX_SPEED_START) * progress
        mistake_prob = settings.AI_ERROR_RATE_START + (settings.AI_ERROR_RATE_END - settings.AI_ERROR_RATE_START) * progress
        mistake_prob = max(0.0, min(1.0, mistake_prob))
        return ai_react, speed_boost, mistake_prob, progress

    def update_play(self, frame, y_hand):
        if y_hand is None:
            self.no_hand_frames += 1
            if self.no_hand_frames >= self.no_hand_hint_after:
                self.ui.draw_text_center(frame, "Mueve tu mano dentro de la camara", y_offset=260, scale=0.9)
        else:
            self.no_hand_frames = 0
        self.player.update(y_hand)

        ai_react, speed_boost, mistake_prob, progress = self._ai_progress_params()
        self.ai.update(self.ball, ai_react, speed_boost, mistake_prob)

        self.ball.update()

        for ev in self.ball.pop_events():
            if ev[0] == "wall":
                _, x, y = ev
                self.ui.spawn_wall_glow(x, y)

        events = self.ball.check_collisions(self.ai, self.player)
        for ev in events:
            _, x, y, side, _ = ev
            self.ui.spawn_hit_ring(x, y)
            self.ui.pulse_paddle("left" if side == "left" else "right")

        if self.ball.x < 0:
            self.scores[1] += 1
            self.serve_dir = -1
            self.ui.flash_center((0, 190, 0))
            self.start_serve(direction=-1)
        elif self.ball.x > settings.SCREEN_WIDTH:
            self.scores[0] += 1
            self.serve_dir = 1
            self.ui.flash_center((0, 0, 190))
            self.start_serve(direction=1)

        if max(self.scores) >= settings.WINNING_SCORE:
            self.state = settings.GAME_OVER

        # panel de aprendizaje IA (opcional)
        if self.show_ai_panel and settings.AI_PANEL_ENABLED:
            current_max_spd = settings.AI_PADDLE_MAX_SPEED * speed_boost
            self.ui.draw_ai_panel(frame, skill=progress, react=ai_react, max_spd=current_max_spd, miss_prob=mistake_prob)

    def update_serve(self, frame):
        t = time.time() - (self.serve_time or time.time())
        frac = max(0.0, min(1.0, t / settings.SERVE_DELAY))
        self.ui.draw_serve_ready(frame, frac)
        if t >= settings.SERVE_DELAY:
            self.state = settings.PLAYING

    def draw_scene(self, frame):
        self.ui.draw_center_line(frame)
        self.ai.draw(frame)
        self.player.draw(frame)
        self.ball.draw(frame)
        self.ui.draw_paddle_pulse(frame, self.ai.rect(), "left")
        self.ui.draw_paddle_pulse(frame, self.player.rect(), "right")
        self.ui.draw_score(frame, self.scores)
        self.ui.draw_rings(frame)
        self.ui.draw_center_pulse(frame)
        self.ui.draw_wall_glows(frame)

    def run(self):
        while True:
            ok, cam = self.cap.read()
            if not ok:
                break

            cam = cv2.flip(cam, 1)
            bg = fast_blur_bgr(cam, scale=0.4, ksize=9)

            y_hand, landmarks, _ = self.detector.process(cam)

            if self.show_skeleton and landmarks:
                self.detector.draw_skeleton(bg, landmarks)

            if self.state == settings.MENU:
                self.ui.draw_menu(bg, "HAND PONG", "Presiona ESPACIO para iniciar")
                menu_elapsed = time.time() - self.menu_time_start
                self.ui.draw_edu_splash_auto(bg, menu_elapsed, force_show=self.force_info_panel)

            elif self.state == settings.SERVE:
                self.update_serve(bg)

            elif self.state == settings.PLAYING:
                self.update_play(bg, y_hand)

            elif self.state == settings.PAUSED:
                self.ui.draw_text_center(bg, "PAUSA - Presiona ESPACIO para continuar", y_offset=0, scale=1.1)

            elif self.state == settings.GAME_OVER:
                winner = "JUGADOR" if self.scores[1] > self.scores[0] else "IA"
                self.ui.draw_text_center(bg, f"GANADOR: {winner} - Presiona R para reiniciar", y_offset=0, scale=1.1)

            self.draw_scene(bg)

            cv2.imshow(self.window_title, bg)
            key = cv2.waitKey(1) & 0xFF

            if key == 27:
                break
            elif key == ord(' '):
                if self.state == settings.MENU:
                    self.start_serve(direction=self.serve_dir)
                else:
                    self.toggle_pause()
            elif key in (ord('r'), ord('R')):
                self.reset_game()
            elif key in (ord('h'), ord('H')):
                self.show_skeleton = not self.show_skeleton
            elif key in (ord('g'), ord('G')):
                self.toggle_fullscreen()
            elif key in (ord('o'), ord('O')):
                self.force_info_panel = not self.force_info_panel
            elif key in (ord('i'), ord('I')):
                self.show_ai_panel = not self.show_ai_panel

        self.cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    GameApp().run()