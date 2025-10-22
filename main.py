# Archivo: main.py - Hand Pong (cv2 + camara + IA humana) VERSION MODULAR
# El texto respeta ASCII (sin acentos en el codigo).

import time
import cv2
import numpy as np

import settings
from hand_detector import HandDetector
from game_objects import Ball, PlayerPaddle, AIPaddle
from opponent_model import OpponentModel
from ui_manager import UIManager
from effects_manager import EffectsManager

WINDOW_NAME = "Hand Pong"
RNG = np.random.default_rng(int(time.time() * 1000) % (2**32))  # RNG con semilla temporal


# ------------------------------------------------------------
# Utilidades
# ------------------------------------------------------------
def fast_blur_bgr(frame, scale=0.4, ksize=9):
    """Desenfoque rapido para el fondo (barato en GPU/CPU)."""
    small = cv2.resize(frame, (0, 0), fx=scale, fy=scale)
    small = cv2.GaussianBlur(small, (ksize | 1, ksize | 1), 0)
    return cv2.resize(small, (frame.shape[1], frame.shape[0]))


def init_video_and_window():
    """Inicializa camara y ventana a pantalla completa si corresponde."""
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: no se pudo acceder a la camara.")
        return None
    cv2.namedWindow(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN)
    if settings.FULLSCREEN:
        cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    return cap


def adaptive_ai_params(scores):
    """
    Ajuste dinamico de reactividad y error segun marcador.
    scores: [ia, jugador]
    """
    diff = int(scores[1] - scores[0])  # jugador - IA
    t = np.clip((diff + 3) / 6.0, 0.0, 1.0)
    err = (1 - t) * settings.AI_ADAPT_ERR_MIN + t * settings.AI_ADAPT_ERR_MAX
    react = (1 - t) * settings.AI_ADAPT_REACT_MAX + t * settings.AI_ADAPT_REACT_MIN
    return float(react), float(err)


def handle_controls(key, state):
    """
    Teclas: ESC, R, ESPACIO/I
    state: dict con llaves 'scores', 'ball', 'round_start', 'show_edu'
    """
    if key == 27:  # ESC
        state["running"] = False
    elif key == ord("r"):
        state["scores"] = [0, 0]
        state["ball"].reset()
        state["round_start"] = time.time()
        # reinicia saque
        state["serving"] = True
        state["serve_time"] = time.time() + settings.SERVE_COUNTDOWN_SEC
        state["next_direction"] = 1 if RNG.random() > 0.5 else -1
    elif key == ord(" ") or key == ord("i"):
        state["show_edu"] = not state["show_edu"]
    return state


def capture_and_prepare_frame(cap):
    ret, frame = cap.read()
    if not ret:
        return None, None
    frame = cv2.flip(frame, 1)
    frame = cv2.resize(frame, (settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
    bg = fast_blur_bgr(frame, 0.4, 9)
    return frame, bg


def update_tips(state):
    """Rota mensajes educativos cada 6s."""
    if time.time() - state["tip_t"] > 6.0:
        state["tip_t"] = time.time()
        state["tip_i"] = (state["tip_i"] + 1) % len(state["tips"])


def do_serve_if_needed(state, ui):
    """Cuenta regresiva y pone la pelota en juego cuando corresponda."""
    if not state["serving"]:
        return
    secs = state["serve_time"] - time.time()
    if secs > 0:
        ui.draw_countdown(state["bg"], secs)
    else:
        state["serving"] = False
        state["ball"].reset(direction=state["next_direction"])


def update_player_from_hand(detector, frame, player):
    """Actualiza paleta jugador con la deteccion de mano."""
    y_hand, landmarks, _ = detector.process(frame)
    if settings.SHOW_HAND_SKELETON and landmarks is not None:
        detector.draw_skeleton(frame, landmarks)
    if y_hand is not None:
        player.update(y_hand)
    return y_hand


def update_ai_and_ball(state, ai_model, ai_paddle, player_paddle, fx, ui, dt):
    """Actualiza logica: pelota, colisiones, IA (prediccion + PD) y puntuacion."""
    ball = state["ball"]
    scores = state["scores"]

    # parametros IA adaptativos
    ai_react, ai_err = adaptive_ai_params(scores)

    # pelota
    ball.update(dt)
    events = ball.check_collisions(ai_paddle, player_paddle, dt=dt)
    for e in events:
        if e[0] == "hit":
            x, y, side = e[1], e[2], e[3]
            ui.spawn_hit_ring(x, y)
            fx.spawn_particles(x, y, (255, 255, 255))
            if side == "player":
                fx.flash_paddle(player_paddle.x, player_paddle.y, player_paddle.width, player_paddle.height, color=player_paddle.color)
            else:
                fx.flash_paddle(ai_paddle.x, ai_paddle.y, ai_paddle.width, ai_paddle.height, color=ai_paddle.color)

    # IA: decide objetivo y avanza PD
    y_target, _ = ai_model.think(ball, ai_paddle, scores, dt)

    # si ya esta cerca, baja reactividad para estabilizar
    err_pix = abs((ai_paddle.y + ai_paddle.height / 2.0) - y_target)
    k = float(np.clip(1.0 - (err_pix / 220.0), 0.0, 1.0))
    ai_react = ai_react * (0.85 + 0.30 * k)

    ai_paddle.target_y = y_target
    ai_paddle.update(ball, reactivity=ai_react, boost=1.0, error_rate=ai_err, dt=dt)

    # puntuacion y reinicio de saque
    if ball.x + ball.radius < 0:
        scores[1] += 1
        ui.flash_color((0, 200, 0))
        fx.spawn_particles(ball.x, ball.y, (0, 200, 0))
        state["serving"] = True
        state["serve_time"] = time.time() + settings.SERVE_COUNTDOWN_SEC
        state["next_direction"] = 1
    elif ball.x - ball.radius > settings.SCREEN_WIDTH:
        scores[0] += 1
        ui.flash_color((200, 0, 0))
        fx.spawn_particles(ball.x, ball.y, (200, 0, 0))
        state["serving"] = True
        state["serve_time"] = time.time() + settings.SERVE_COUNTDOWN_SEC
        state["next_direction"] = -1


def render_scene(state, ui, fx, ai_model, ai_paddle, player_paddle, ball):
    """Dibuja todos los elementos en el frame de salida."""
    bg = state["bg"]

    # linea educativa de prediccion
    if not state["serving"] and settings.EDUCATIONAL_MODE and state["show_pred"]:
        y_pred_draw = ai_model.get_last_clean_prediction_y()
        x0 = int(ai_paddle.x + ai_paddle.width)
        cv2.line(bg, (x0, int(y_pred_draw)), (x0 + 60, int(y_pred_draw)), (0, 255, 0), 2)

    # objetos
    ai_paddle.draw(bg)
    player_paddle.draw(bg)
    ball.draw(bg)

    # UI y FX
    ui.draw_score(bg, state["scores"])
    fx.draw(bg)
    if state["show_edu"] and state["tips"]:
        ui.draw_edu_panel(bg, state["tips"][state["tip_i"]])

    # mostrar
    cv2.imshow(WINDOW_NAME, bg)


def check_round_end_and_reset(state):
    """Comprueba fin de ronda por tiempo o marcador y resetea si corresponde."""
    time_up = (time.time() - state["round_start"]) > settings.ROUND_DURATION_SEC
    reached = any(s >= settings.WINNING_SCORE for s in state["scores"])
    if not (time_up or reached):
        return

    winner = "IA" if state["scores"][0] > state["scores"][1] else "Jugador"
    msg = f"Ganador: {winner}"
    cv2.putText(
        state["bg"], msg,
        (int(settings.SCREEN_WIDTH * 0.32), int(settings.SCREEN_HEIGHT * 0.5)),
        settings.FONT, 2, (255, 255, 255), 4, cv2.LINE_AA
    )
    cv2.imshow(WINDOW_NAME, state["bg"])
    cv2.waitKey(1200)

    # reset
    state["scores"] = [0, 0]
    state["serving"] = True
    state["serve_time"] = time.time() + settings.SERVE_COUNTDOWN_SEC
    state["round_start"] = time.time()
    state["next_direction"] = 1 if RNG.random() > 0.5 else -1


# ------------------------------------------------------------
# Programa principal
# ------------------------------------------------------------
def main():
    print("Iniciando Hand Pong...")
    cap = init_video_and_window()
    if cap is None:
        return

    # instancias
    detector = HandDetector()
    ui = UIManager()
    fx = EffectsManager()
    ai_model = OpponentModel()
    ball = Ball()
    player = PlayerPaddle(
        x_pos=settings.SCREEN_WIDTH - settings.PADDLE_WIDTH - 60,
        color=settings.PADDLE_R_COLOR,
    )
    ai = AIPaddle(x_pos=60, color=settings.PADDLE_L_COLOR)

    # estado del juego
    state = {
        "running": True,
        "scores": [0, 0],          # [IA, Jugador]
        "serving": True,
        "serve_time": time.time() + settings.SERVE_COUNTDOWN_SEC,
        "round_start": time.time(),
        "next_direction": 1,
        "show_edu": True,
        "show_pred": settings.EDUCATIONAL_MODE,
        "tips": [
            "La camara ve tu mano y la convierte en coordenadas.",
            "La IA predice donde golpeara la pelota.",
            "La IA comete errores al inicio y los reduce.",
            "Cada golpe acelera ligeramente la pelota.",
            "Tu mano controla la paleta derecha.",
        ],
        "tip_i": 0,
        "tip_t": time.time(),
        "ball": ball,
    }

    fps_cap = int(getattr(settings, "FPS_CAP", 60))
    frame_delay = 1.0 / max(30, fps_cap)

    prev_t = time.perf_counter()

    while state["running"]:
        loop_t = time.perf_counter()
        dt = loop_t - prev_t
        prev_t = loop_t
        if dt > 0.05:
            dt = 0.05

        # frame
        frame, bg = capture_and_prepare_frame(cap)
        if frame is None:
            print("Error: no se recibe video de la camara.")
            break
        state["bg"] = bg  # guardar referencia para funciones que dibujan

        # UI: cuenta regresiva de saque
        if state["serving"]:
            do_serve_if_needed(state, ui)
        else:
            # deteccion de mano y movimiento jugador
            update_player_from_hand(detector, frame, player)
            # logica de IA y pelota
            update_ai_and_ball(state, ai_model, ai, player, fx, ui, dt)

        # rotacion de mensajes
        update_tips(state)

        # render y controles
        render_scene(state, ui, fx, ai_model, ai, player, ball)
        key = cv2.waitKey(1) & 0xFF
        state = handle_controls(key, state)

        # fin de ronda
        check_round_end_and_reset(state)

        # limitar FPS
        spent = time.time() - loop_t
        wait = frame_delay - spent
        if wait > 0:
            time.sleep(wait)

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()