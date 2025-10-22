# Archivo: main.py - Hand Pong feria (dt, swept, intercepcion, countdown)
# ASCII puro

import cv2
import time
import numpy as np
import settings
from hand_detector import HandDetector
from game_objects import Ball, PlayerPaddle, AIPaddle
from opponent_model import OpponentModel
from ui_manager import UIManager
from effects_manager import EffectsManager

WINDOW_NAME = "Hand Pong"


def fast_blur_bgr(frame, scale=0.4, ksize=9):
    small = cv2.resize(frame, (0, 0), fx=scale, fy=scale)
    small = cv2.GaussianBlur(small, (ksize | 1, ksize | 1), 0)
    return cv2.resize(small, (frame.shape[1], frame.shape[0]))


def init_video_and_window():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: no se pudo acceder a la camara.")
        return None
    cv2.namedWindow(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    return cap


def adaptive_ai_params(scores):
    diff = int(scores[1] - scores[0])  # jugador - IA
    t = np.clip((diff + 3) / 6.0, 0.0, 1.0)
    err = (1 - t) * settings.AI_ADAPT_ERR_MIN + t * settings.AI_ADAPT_ERR_MAX
    react = (1 - t) * settings.AI_ADAPT_REACT_MAX + t * settings.AI_ADAPT_REACT_MIN
    return float(react), float(err)


def handle_controls(key, scores, ball, round_start, show_edu):
    running = True
    if key == 27:
        running = False
    elif key == ord("r"):
        scores[:] = [0, 0]
        ball.reset()
        round_start = time.time()
    elif key == ord("i") or key == ord(" "):
        show_edu = not show_edu
    return running, scores, ball, round_start, show_edu


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

    scores = [0, 0]   # [IA, Jugador]
    show_edu = True
    show_pred = settings.EDUCATIONAL_MODE

    tips = [
        "La camara ve tu mano y la convierte en coordenadas.",
        "La IA predice donde golpeara la pelota.",
        "La IA comete errores al inicio y los reduce.",
        "Cada golpe acelera ligeramente la pelota.",
        "Tu mano controla la paleta derecha."
    ]
    tip_i = 0
    tip_t = time.time()

    round_start = time.time()
    serving = True
    serve_time = time.time() + settings.SERVE_COUNTDOWN_SEC
    next_direction = 1

    fps_cap = int(getattr(settings, "FPS_CAP", 60))
    frame_delay = 1.0 / max(30, fps_cap)

    prev_t = time.perf_counter()

    while True:
        loop_t = time.perf_counter()
        dt = loop_t - prev_t
        prev_t = loop_t
        if dt > 0.05:
            dt = 0.05

        ret, frame = cap.read()
        if not ret:
            print("Error: no se recibe video de la camara.")
            break

        frame = cv2.flip(frame, 1)
        frame = cv2.resize(frame, (settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
        bg = fast_blur_bgr(frame, 0.4, 9)

        y_hand, landmarks, _ = detector.process(frame)
        if settings.SHOW_HAND_SKELETON and landmarks is not None:
            detector.draw_skeleton(bg, landmarks)

        if serving:
            secs = serve_time - time.time()
            if secs > 0:
                ui.draw_countdown(bg, secs)
            else:
                serving = False
                ball.reset(direction=next_direction)
        else:
            if y_hand is not None:
                player.update(y_hand)

            ai_react, ai_err = adaptive_ai_params(scores)

            ball.update(dt)
            events = ball.check_collisions(ai, player, dt=dt)
            for e in events:
                if e[0] == "hit":
                    x, y, side = e[1], e[2], e[3]
                    ui.spawn_hit_ring(x, y)
                    fx.spawn_particles(x, y, (255, 255, 255))
                    if side == "player":
                        fx.flash_paddle(player.x, player.y, player.width, player.height, color=player.color)
                    else:
                        fx.flash_paddle(ai.x, ai.y, ai.width, ai.height, color=ai.color)

            ai_face_x = ai.x + ai.width
            y_pred = ai_model.predict_intercept_at_x(ball, ai_face_x)
            y_pred = ai_model.apply_error(y_pred, ai_err)
            err_pix = abs((ai.y + ai.height / 2.0) - y_pred)
            k = float(np.clip(1.0 - (err_pix / 200.0), 0.0, 1.0))
            ai_react = ai_react * (0.85 + 0.30 * k)
            ai.target_y = y_pred
            ai.update(ball, reactivity=ai_react, boost=1.0, error_rate=ai_err)

            if ball.x < 0:
                scores[1] += 1
                ui.flash_color((0, 200, 0))
                fx.spawn_particles(ball.x, ball.y, (0, 200, 0))
                serving = True
                serve_time = time.time() + settings.SERVE_COUNTDOWN_SEC
                next_direction = 1  # saca hacia IA (derecha)
            elif ball.x > settings.SCREEN_WIDTH:
                scores[0] += 1
                ui.flash_color((200, 0, 0))
                fx.spawn_particles(ball.x, ball.y, (200, 0, 0))
                serving = True
                serve_time = time.time() + settings.SERVE_COUNTDOWN_SEC
                next_direction = -1  # saca hacia jugador (izquierda)

        if time.time() - tip_t > 6.0:
            tip_t = time.time()
            tip_i = (tip_i + 1) % len(tips)
        edu_text = tips[tip_i] if show_edu else ""

        time_up = (time.time() - round_start) > settings.ROUND_DURATION_SEC
        reached = any(s >= settings.WINNING_SCORE for s in scores)
        if time_up or reached:
            winner = "IA" if scores[0] > scores[1] else "Jugador"
            msg = f"Ganador: {winner}"
            cv2.putText(bg, msg, (int(settings.SCREEN_WIDTH * 0.32), int(settings.SCREEN_HEIGHT * 0.5)),
                        settings.FONT, 2, (255, 255, 255), 4, cv2.LINE_AA)
            cv2.imshow(WINDOW_NAME, bg)
            cv2.waitKey(1200)
            scores = [0, 0]
            serving = True
            serve_time = time.time() + settings.SERVE_COUNTDOWN_SEC
            round_start = time.time()
            next_direction = 1 if np.random.rand() > 0.5 else -1

        y_pred_draw = ai.get_last_target_y() if not serving and show_pred else None
        ai.draw(bg)
        player.draw(bg)
        ball.draw(bg)
        if y_pred_draw is not None:
            x0 = int(ai.x + ai.width)
            cv2.line(bg, (x0, int(y_pred_draw)), (x0 + 60, int(y_pred_draw)), (0, 255, 0), 2)
        ui.draw_score(bg, scores)
        fx.draw(bg)
        if edu_text:
            ui.draw_edu_panel(bg, edu_text)

        cv2.imshow(WINDOW_NAME, bg)
        key = cv2.waitKey(1) & 0xFF
        running, scores, ball, round_start, show_edu = handle_controls(
            key, scores, ball, round_start, show_edu
        )
        if not running:
            break

        spent = time.time() - loop_t
        wait = frame_delay - spent
        if wait > 0:
            time.sleep(wait)

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()