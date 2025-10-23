# Archivo: main.py - Hand Pong (cv2 + camara + IA con menu clasico)
# ASCII puro

import time
import cv2
import numpy as np

import settings
from hand_detector import HandDetector
from game_objects import Ball, PlayerPaddle, AIPaddle
from opponent_model import OpponentModel
from ui_manager import UIManager
from effects_manager import EffectsManager


class AISkillManager:
    def __init__(self):
        self.elapsed = 0.0

    def reset(self):
        self.elapsed = 0.0

    def update(self, dt, scores):
        self.elapsed += max(0.0, dt)
        start = settings.AI_SKILL_START
        end = settings.AI_SKILL_END
        t = np.clip(self.elapsed / max(1.0, settings.AI_TIME_TO_SKILL), 0.0, 1.0)
        diff = scores[1] - scores[0]
        s = np.clip((diff + 3) / 6.0, 0.0, 1.0)
        blend = np.clip(0.4 * t + 0.6 * s, 0.0, 1.0)

        cur = {}
        for k in start:
            a, b = float(start[k]), float(end.get(k, start[k]))
            cur[k] = a + (b - a) * blend
        cur["blend"] = blend
        return cur


def fast_blur_bgr(frame, scale=0.35, ksize=9):
    small = cv2.resize(frame, (0, 0), fx=scale, fy=scale)
    small = cv2.GaussianBlur(small, (ksize | 1, ksize | 1), 0)
    return cv2.resize(small, (frame.shape[1], frame.shape[0]))


def init_video_and_window():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: no se pudo acceder a la camara.")
        return None
    cv2.namedWindow(settings.WINDOW_NAME, cv2.WND_PROP_FULLSCREEN)
    if settings.FULLSCREEN:
        cv2.setWindowProperty(settings.WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    return cap


def capture_frame(cap):
    ret, frame = cap.read()
    if not ret:
        return None, None
    frame = cv2.flip(frame, 1)
    frame = cv2.resize(frame, (settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
    bg = fast_blur_bgr(frame)
    return frame, bg


def compute_reactivity(scores, blend):
    diff = scores[1] - scores[0]
    base = 0.045 + 0.015 * np.clip(diff, -3, 3)
    boost = 0.04 * blend
    return float(np.clip(base + boost, 0.02, 0.16))


def do_serve(state, ui):
    if not state["serving"]:
        return
    secs = state["serve_time"] - time.time()
    if secs > 0:
        ui.draw_countdown(state["bg"], secs)
    else:
        state["serving"] = False
        state["ball"].reset(direction=state["next_direction"])


def update_ticker(state):
    now = time.time()
    if now - state["tip_time"] > settings.TICKER_INTERVAL:
        state["tip_time"] = now
        state["tip_index"] = (state["tip_index"] + 1) % len(state["tips"])


def update_ai_logic(state, ai_model, ai_paddle, player_paddle, fx, ui, dt, skill_manager):
    ball = state["ball"]
    scores = state["scores"]

    # evolucion de habilidad IA
    skill = skill_manager.update(dt, scores)
    ai_model.set_skill(**{k: v for k, v in skill.items() if k in {"miss_base", "lat_ms", "decision_hz", "sacc_amp_px"}})

    # pelota y colisiones
    ball.update(dt)
    events = ball.check_collisions(ai_paddle, player_paddle)
    for tag, x, y, side in events:
        if tag == "hit":
            ui.spawn_hit_ring(x, y)  # anillo de impacto
            fx.spawn_particles(x, y, (255, 255, 255))
            # flash en paleta
            if side == "player":
                fx.flash_paddle(player_paddle.x, player_paddle.y, player_paddle.width, player_paddle.height, color=(255, 255, 255))
            else:
                fx.flash_paddle(ai_paddle.x, ai_paddle.y, ai_paddle.width, ai_paddle.height, color=(255, 255, 255))

    # IA: decide objetivo y avanza PD
    target_y, info = ai_model.think(ball, ai_paddle, scores, dt)
    reactivity = compute_reactivity(scores, skill["blend"])
    ai_paddle.update(reactivity, target_y, dt, np.hypot(ball.vx, ball.vy))

    # telemetria
    state["telemetry"] = {
        "ball_speed": float(np.hypot(ball.vx, ball.vy)),
        "p_miss": float(info.get("p_miss", skill.get("miss_base", 0.0))),
        "lat_ms": float(info.get("lat_ms", skill.get("lat_ms", settings.AI_LATENCY_MS))),
        "decision_hz": float(skill.get("decision_hz", settings.AI_DECISION_RATE_HZ)),
    }

    # puntuacion y saque
    if ball.x + ball.radius < 0:
        scores[1] += 1
        ui.flash_color((0, 200, 0))
        fx.spawn_particles(ball.x, ball.y, (0, 200, 0))
        state["serving"] = True
        state["serve_time"] = time.time() + settings.SERVE_COUNTDOWN_SEC
        state["next_direction"] = 1
        skill_manager.reset()
    elif ball.x - ball.radius > settings.SCREEN_WIDTH:
        scores[0] += 1
        ui.flash_color((200, 0, 0))
        fx.spawn_particles(ball.x, ball.y, (200, 0, 0))
        state["serving"] = True
        state["serve_time"] = time.time() + settings.SERVE_COUNTDOWN_SEC
        state["next_direction"] = -1
        skill_manager.reset()


def render_game(state, ui, fx, ai_model, ai_paddle, player_paddle):
    frame = state["bg"].copy()

    # linea de prediccion educativa (opcional)
    if settings.EDUCATIONAL_MODE and state["show_prediction"] and not state["serving"]:
        y_pred = ai_model.get_last_clean_prediction_y()
        x0 = int(ai_paddle.x + ai_paddle.width)
        cv2.line(frame, (x0, int(y_pred)), (x0 + 60, int(y_pred)), (0, 255, 0), 2)

    # objetos
    ai_paddle.draw(frame)
    player_paddle.draw(frame)
    state["ball"].draw(frame)

    # HUD y marcador
    ui.draw_score(frame, state["scores"])
    fx.draw(frame)

    if state["show_hud"]:
        ui.draw_hud(frame, state.get("telemetry"))

    # panel educativo inferior o ticker
    if state["show_edu"]:
        ui.draw_edu_panel(frame, state["tips"][state["tip_index"]])

    cv2.imshow(settings.WINDOW_NAME, frame)


def render_menu(state, ui):
    frame = state["bg"].copy()
    ui.draw_menu(frame)
    cv2.imshow(settings.WINDOW_NAME, frame)


def handle_controls(key, state):
    # ESC
    if key == 27:
        state["running"] = False
    # espacio: alterna pausa/juego o sale del menu
    elif key == ord(" "):
        if state["in_menu"]:
            state["in_menu"] = False
            state["serving"] = True
            state["serve_time"] = time.time() + settings.SERVE_COUNTDOWN_SEC
        else:
            state["paused"] = not state["paused"]
    # reiniciar
    elif key == ord("r"):
        state["scores"] = [0, 0]
        state["ball"].reset(direction=1)
        state["round_start"] = time.time()
        state["serving"] = True
        state["serve_time"] = time.time() + settings.SERVE_COUNTDOWN_SEC
        state["next_direction"] = 1
    # panel educativo
    elif key == ord("i"):
        state["show_edu"] = not state["show_edu"]
    # HUD
    elif key == ord("h"):
        state["show_hud"] = not state["show_hud"]
    # prediccion IA
    elif key == ord("l"):
        state["show_prediction"] = not state["show_prediction"]


def check_round_end(state):
    time_up = (time.time() - state["round_start"]) > settings.ROUND_DURATION_SEC
    reach_score = any(score >= settings.WINNING_SCORE for score in state["scores"])
    if not (time_up or reach_score):
        return False

    winner = "IA" if state["scores"][0] > state["scores"][1] else "Jugador"
    frame = state["bg"].copy()
    cv2.putText(
        frame,
        f"Ganador: {winner}",
        (int(settings.SCREEN_WIDTH * 0.32), int(settings.SCREEN_HEIGHT * 0.52)),
        settings.FONT,
        2.2,
        (255, 255, 255),
        5,
        cv2.LINE_AA,
    )
    cv2.imshow(settings.WINDOW_NAME, frame)
    cv2.waitKey(1200)

    # reset para siguiente partida corta (feria)
    state["scores"] = [0, 0]
    state["serving"] = True
    state["serve_time"] = time.time() + settings.SERVE_COUNTDOWN_SEC
    state["round_start"] = time.time()
    state["next_direction"] = 1
    state["ball"].reset(direction=1)
    return True


def main():
    print("Iniciando Hand Pong...")
    cap = init_video_and_window()
    if cap is None:
        return

    detector = HandDetector()
    ui = UIManager()
    fx = EffectsManager()
    ai_model = OpponentModel()
    ball = Ball()
    player = PlayerPaddle(x_pos=settings.SCREEN_WIDTH - settings.PADDLE_WIDTH - 60, color=settings.PADDLE_R_COLOR)
    ai = AIPaddle(x_pos=60, color=settings.PADDLE_L_COLOR)
    skill_manager = AISkillManager()

    state = {
        "running": True,
        "in_menu": True,
        "paused": False,
        "scores": [0, 0],  # [IA, Jugador]
        "serving": False,
        "serve_time": time.time() + settings.SERVE_COUNTDOWN_SEC,
        "next_direction": 1,
        "round_start": time.time(),
        "ball": ball,
        "show_edu": True,
        "show_hud": True,
        "show_prediction": settings.EDUCATIONAL_MODE,
        "tips": [
            "La camara sigue la altura de tu mano.",
            "La IA predice rebotes y ajusta su paleta.",
            "Cada golpe puede anadir spin y acelerar la pelota.",
            "Observa la linea verde de prediccion de la IA.",
        ],
        "tip_index": 0,
        "tip_time": time.time(),
        "telemetry": None,
    }

    fps_cap = max(30, getattr(settings, "FPS_CAP", 60))
    frame_delay = 1.0 / fps_cap
    prev_t = time.perf_counter()

    while state["running"]:
        frame, bg = capture_frame(cap)
        if frame is None:
            print("Error: no se recibe video de la camara.")
            break
        state["bg"] = bg

        loop_t = time.perf_counter()
        dt = loop_t - prev_t
        prev_t = loop_t
        dt = min(dt, 0.05)

        if state["in_menu"]:
            render_menu(state, ui)
        else:
            if state["serving"]:
                do_serve(state, ui)

            # deteccion de mano y control jugador
            y_hand, landmarks, valid = detector.process(frame)
            if settings.SHOW_HAND_SKELETON and valid:
                detector.draw_skeleton(frame, landmarks)
            player.update(y_hand)

            if not state["serving"] and not state["paused"]:
                update_ai_logic(state, ai_model, ai, player, fx, ui, dt, skill_manager)

            update_ticker(state)
            render_game(state, ui, fx, ai_model, ai, player)

        key = cv2.waitKey(1) & 0xFF
        handle_controls(key, state)

        if not state["in_menu"] and check_round_end(state):
            skill_manager.reset()

        # limitar FPS
        spent = time.time() - loop_t
        wait = frame_delay - spent
        if wait > 0:
            time.sleep(wait)

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()