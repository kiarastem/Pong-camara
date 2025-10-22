# Archivo: main.py - Hand Pong (cv2 + camara + IA humana)
# ASCII puro (sin acentos en el codigo)

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
        diff = scores[1] - scores[0]  # jugador - IA
        s = np.clip((diff + 3) / 6.0, 0.0, 1.0)
        blend = np.clip(0.4 * t + 0.6 * s, 0.0, 1.0)
        cur = {}
        for k in start:
            cur[k] = float(start[k] + (end.get(k, start[k]) - start[k]) * blend)
        cur["blend"] = float(blend)
        return cur


def fast_blur_bgr(frame, scale=0.35, ksize=9):
    small = cv2.resize(frame, (0, 0), fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    small = cv2.GaussianBlur(small, (ksize | 1, ksize | 1), 0)
    return cv2.resize(small, (frame.shape[1], frame.shape[0]), interpolation=cv2.INTER_LINEAR)


def init_video_and_window():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: no se pudo acceder a la camara.")
        return None
    cv2.namedWindow(settings.WINDOW_NAME, cv2.WND_PROP_FULLSCREEN)
    if settings.FULLSCREEN:
        cv2.setWindowProperty(settings.WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    return cap


def compute_reactivity(scores, blend):
    diff = scores[1] - scores[0]  # jugador - IA
    base = 0.045 + 0.015 * np.clip(diff, -3, 3)
    boost = 0.04 * blend
    return float(np.clip(base + boost, 0.02, 0.18))


def capture_frame(cap):
    ret, frame = cap.read()
    if not ret:
        return None, None
    frame = cv2.flip(frame, 1)
    frame = cv2.resize(frame, (settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
    bg = fast_blur_bgr(frame)
    return frame, bg


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

    skill = skill_manager.update(dt, scores)
    ai_model.set_skill(**{k: v for k, v in skill.items() if k in {"miss_base", "lat_ms", "decision_hz", "sacc_amp_px"}})

    ball.update(dt)
    events = ball.check_collisions(ai_paddle, player_paddle)
    for evt in events:
        tag, x, y, side = evt
        if tag == "hit":
            ui.spawn_hit_ring(x, y)
            fx.spawn_particles(x, y, (255, 255, 255))
            p = player_paddle if side == "player" else ai_paddle
            fx.flash_paddle(p.x, p.y, p.width, p.height, p.color)

    target_y, info = ai_model.think(ball, ai_paddle, scores, dt)
    reactivity = compute_reactivity(scores, skill["blend"])
    ai_paddle.update(reactivity, target_y, dt, np.hypot(ball.vx, ball.vy))

    telemetry = {
        "ball_speed": float(np.hypot(ball.vx, ball.vy)),
        "p_miss": float(info.get("p_miss", skill.get("miss_base", 0.0))),
        "lat_ms": float(info.get("lat_ms", skill.get("lat_ms", settings.AI_LATENCY_MS))),
        "decision_hz": float(skill.get("decision_hz", settings.AI_DECISION_RATE_HZ)),
    }
    state["telemetry"] = telemetry

    # puntos
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


def render(state, ui, fx, ai_model, ai_paddle, player_paddle):
    frame = state["bg"].copy()

    if settings.EDUCATIONAL_MODE and state["show_prediction"] and not state["serving"]:
        y_pred = ai_model.get_last_clean_prediction_y()
        x0 = int(ai_paddle.x + ai_paddle.width)
        cv2.line(frame, (x0, int(y_pred)), (x0 + 60, int(y_pred)), (0, 255, 0), 2)

    ai_paddle.draw(frame)
    player_paddle.draw(frame)
    state["ball"].draw(frame)

    ui.draw_score(frame, state["scores"])
    fx.draw(frame)

    if state["show_hud"]:
        tuning = {
            "AI_PADDLE_MAX_SPEED": state["tuning"]["AI_PADDLE_MAX_SPEED"],
            "AI_D_GAIN": state["tuning"]["AI_D_GAIN"],
            "AI_DEADBAND_PX": state["tuning"]["AI_DEADBAND_PX"],
            "AI_MAX_ACCEL": state["tuning"]["AI_MAX_ACCEL"],
        }
        ui.draw_hud(frame, state.get("telemetry"), tuning)

    if state["show_edu"]:
        ui.draw_edu_panel(frame, state["tips"][state["tip_index"]])
    else:
        ui.draw_ticker(frame, state["tips"][state["tip_index"]])

    cv2.imshow(settings.WINDOW_NAME, frame)


def handle_controls(key, state, detector):
    # salir
    if key == 27:
        state["running"] = False
        return

    # reset
    if key == ord("r"):
        state["scores"] = [0, 0]
        state["serving"] = True
        state["serve_time"] = time.time() + settings.SERVE_COUNTDOWN_SEC
        state["next_direction"] = 1
        state["round_start"] = time.time()
        state["ball"].reset(direction=1)
        return

    # toggles
    if key in (ord(" "), ord("i")):
        state["show_edu"] = not state["show_edu"]
    if key == ord("h"):
        state["show_hud"] = not state["show_hud"]
    if key == ord("l"):
        state["show_prediction"] = not state["show_prediction"]
    if key == ord("k"):
        state["show_skeleton"] = not state["show_skeleton"]
    if key == ord("c"):
        detector.calibrate_center()

    # tuning en vivo (Q/A, W/S, E/D, Z/X)
    step_speed = 80.0
    step_acc = 200.0
    step_dead = 1.0
    step_d = 0.01

    if key == ord("q"):
        state["tuning"]["AI_PADDLE_MAX_SPEED"] = max(600.0, state["tuning"]["AI_PADDLE_MAX_SPEED"] - step_speed)
    if key == ord("a"):
        state["tuning"]["AI_PADDLE_MAX_SPEED"] = min(3200.0, state["tuning"]["AI_PADDLE_MAX_SPEED"] + step_speed)

    if key == ord("w"):
        state["tuning"]["AI_D_GAIN"] = max(0.0, state["tuning"]["AI_D_GAIN"] - step_d)
    if key == ord("s"):
        state["tuning"]["AI_D_GAIN"] = min(1.0, state["tuning"]["AI_D_GAIN"] + step_d)

    if key == ord("e"):
        state["tuning"]["AI_DEADBAND_PX"] = max(0.0, state["tuning"]["AI_DEADBAND_PX"] - step_dead)
    if key == ord("d"):
        state["tuning"]["AI_DEADBAND_PX"] = min(40.0, state["tuning"]["AI_DEADBAND_PX"] + step_dead)

    if key == ord("z"):
        state["tuning"]["AI_MAX_ACCEL"] = max(800.0, state["tuning"]["AI_MAX_ACCEL"] - step_acc)
    if key == ord("x"):
        state["tuning"]["AI_MAX_ACCEL"] = min(9000.0, state["tuning"]["AI_MAX_ACCEL"] + step_acc)


def check_round_end(state):
    time_up = (time.time() - state["round_start"]) > settings.ROUND_DURATION_SEC
    reach_score = any(score >= settings.WINNING_SCORE for score in state["scores"])
    if not (time_up or reach_score):
        return False

    winner = "IA" if state["scores"][0] > state["scores"][1] else "Jugador"
    msg = f"Ganador: {winner}"
    frame = state["bg"].copy()
    cv2.putText(
        frame,
        msg,
        (int(settings.SCREEN_WIDTH * 0.32), int(settings.SCREEN_HEIGHT * 0.52)),
        settings.FONT,
        2.2,
        (255, 255, 255),
        5,
        cv2.LINE_AA,
    )
    cv2.imshow(settings.WINDOW_NAME, frame)
    cv2.waitKey(1200)

    # reset
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
        "scores": [0, 0],
        "serving": True,
        "serve_time": time.time() + settings.SERVE_COUNTDOWN_SEC,
        "next_direction": 1,
        "round_start": time.time(),
        "ball": ball,
        "show_edu": True,
        "show_hud": settings.HUD_VISIBLE,
        "show_prediction": settings.EDUCATIONAL_MODE,
        "show_skeleton": settings.SHOW_HAND_SKELETON,
        "tips": [
            "La camara sigue la altura de tu mano en tiempo real.",
            "La IA predice rebotes y corrige con retraso humano.",
            "Cada golpe agrega spin y acelera un poco la pelota.",
            "El HUD muestra velocidad, error esperado y latencia.",
            "La IA aprende mas rapido si el jugador toma ventaja.",
        ],
        "tip_index": 0,
        "tip_time": time.time(),
        "telemetry": None,
        "tuning": {
            "AI_PADDLE_MAX_SPEED": float(settings.AI_PADDLE_MAX_SPEED),
            "AI_D_GAIN": float(settings.AI_D_GAIN),
            "AI_DEADBAND_PX": float(settings.AI_DEADBAND_PX),
            "AI_MAX_ACCEL": float(settings.AI_MAX_ACCEL),
        },
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

        # aplicar tuning en runtime
        settings.AI_PADDLE_MAX_SPEED = state["tuning"]["AI_PADDLE_MAX_SPEED"]
        settings.AI_D_GAIN = state["tuning"]["AI_D_GAIN"]
        settings.AI_DEADBAND_PX = state["tuning"]["AI_DEADBAND_PX"]
        settings.AI_MAX_ACCEL = state["tuning"]["AI_MAX_ACCEL"]

        if state["serving"]:
            do_serve(state, ui)
        else:
            y_hand, landmarks, valid = detector.process(frame, dt)
            if state["show_skeleton"] and valid:
                detector.draw_skeleton(frame, landmarks)
            player.update(y_hand)
            update_ai_logic(state, ai_model, ai, player, fx, ui, dt, skill_manager)

        update_ticker(state)
        render(state, ui, fx, ai_model, ai, player)

        key = cv2.waitKey(1) & 0xFF
        if key != 255:
            handle_controls(key, state, detector)

        if check_round_end(state):
            skill_manager.reset()

        spent = time.time() - loop_t
        wait = frame_delay - spent
        if wait > 0:
            time.sleep(wait)

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()