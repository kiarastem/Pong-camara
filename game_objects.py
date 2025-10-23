# game_objects.py
# Version educativa y optimizada para feria

import cv2
import random
import time
import settings


def clamp(value, min_value, max_value):
    return max(min_value, min(value, max_value))


class Paddle:
    """Clase base para las paletas."""
    def __init__(self, x_pos, color):
        self.width = settings.PADDLE_WIDTH
        self.height = settings.PADDLE_HEIGHT
        self.x = x_pos
        self.y = (settings.SCREEN_HEIGHT - self.height) / 2
        self.color = color

    def rect(self):
        return int(self.x), int(self.y), int(self.width), int(self.height)

    def draw(self, frame):
        cv2.rectangle(frame, (int(self.x), int(self.y)),
                      (int(self.x + self.width), int(self.y + self.height)),
                      self.color, -1)


class PlayerPaddle(Paddle):
    """Paleta controlada por la camara (mano del jugador)."""
    def update(self, y_pos):
        if y_pos is not None:
            self.y = y_pos - self.height / 2
            self.y = clamp(self.y, 0, settings.SCREEN_HEIGHT - self.height)


class AIPaddle(Paddle):
    """Paleta de IA adaptativa con impulso de proximidad."""
    def __init__(self, x_pos, color):
        super().__init__(x_pos, color)
        self._t_prev = time.time()
        self._err_cd = 0.0
        self._aim_bias = 0.0
        self._lat_accum = 0.0
        self._latency_ms = settings.AI_LATENCY_MS / 1000.0
        self._last_target_y = self.y + self.height / 2
        self._noise = 0.0
        self._err_gain_pen = 1.0
        self._err_spd_pen = 1.0
        self.react_gain = 1.0
        self.max_speed_mult = 1.0
        self.err_std = 8.0
        self.rng = random.Random(42)

    def center_y(self):
        return self.y + self.height / 2

    def update(self, ball, reactivity, speed_boost=1.0, mistake_prob=0.0):
        now = time.time()
        dt = max(0.0, min(0.1, now - self._t_prev))
        self._t_prev = now
        self._lat_accum += dt

        # errores intencionales
        if self._err_cd <= 0.0:
            if self.rng.random() < mistake_prob * dt:
                self._err_cd = settings.AI_ERROR_WHIF_TIME
                self._aim_bias = self.rng.normalvariate(0.0, settings.AI_AIM_JITTER_PX)
        else:
            self._err_cd = max(0.0, self._err_cd - dt)

        # actualizar prediccion de posicion
        if self._lat_accum >= self._latency_ms:
            self._lat_accum = 0.0
            target_y = ball.y
            self._noise = 0.9 * self._noise + 0.1 * self.rng.normalvariate(0.0, self.err_std)
            target_y += self._noise
            self._last_target_y = 0.7 * self._last_target_y + 0.3 * (target_y + self._aim_bias)

        # movimiento base
        delta = self._last_target_y - self.center_y()

        # boost de proximidad
        coming = (ball.vel_x < 0 and self.x < settings.SCREEN_WIDTH / 2) or \
                 (ball.vel_x > 0 and self.x > settings.SCREEN_WIDTH / 2)
        eps = 1e-6
        t_me = abs((self.x - ball.x) / (ball.vel_x + eps)) if coming else 999.0
        t_norm = max(0.0, 1.0 - t_me / 0.8) if t_me < 0.8 else 0.0
        proximity_gain = 1.0 + 0.9 * t_norm
        proximity_speed = 1.0 + 0.7 * t_norm

        gain = reactivity * proximity_gain
        move = delta * gain

        max_spd = (settings.AI_PADDLE_MAX_SPEED * speed_boost) * proximity_speed
        move = clamp(move, -max_spd, max_spd)
        self.y = clamp(self.y + move, 0, settings.SCREEN_HEIGHT - self.height)


class Ball:
    """Pelota con rebotes y aceleracion."""
    def __init__(self):
        self.radius = settings.BALL_RADIUS
        self.reset()

    def reset(self, direction=1, randomize_angle=True):
        self.x = settings.SCREEN_WIDTH / 2
        self.y = settings.SCREEN_HEIGHT / 2
        self.vel_x = settings.INITIAL_BALL_SPEED * direction
        self.vel_y = random.uniform(-3, 3) if randomize_angle else 0
        self._events = []

    def update(self):
        self.x += self.vel_x
        self.y += self.vel_y
        if abs(self.vel_x) < settings.BALL_MAX_SPEED:
            self.vel_x *= 1.0008
        if abs(self.vel_y) < settings.BALL_MAX_SPEED:
            self.vel_y *= 1.0005

    def draw(self, frame):
        cv2.circle(frame, (int(self.x), int(self.y)), self.radius, settings.BALL_COLOR, -1)

    def pop_events(self):
        ev, self._events = self._events, []
        return ev

    def check_collisions(self, left_paddle, right_paddle):
        if self.y - self.radius <= 0 or self.y + self.radius >= settings.SCREEN_HEIGHT:
            self.vel_y *= -1
            self._events.append(("wall", self.x, self.y))

        # colision con paleta izquierda
        if (self.vel_x < 0 and
            left_paddle.x < self.x - self.radius < left_paddle.x + left_paddle.width and
            left_paddle.y < self.y < left_paddle.y + left_paddle.height):
            self._handle_hit(left_paddle)

        # colision con paleta derecha
        if (self.vel_x > 0 and
            right_paddle.x < self.x + self.radius < right_paddle.x + right_paddle.width and
            right_paddle.y < self.y < right_paddle.y + right_paddle.height):
            self._handle_hit(right_paddle)

        return self._events

    def _handle_hit(self, paddle):
        self.vel_x *= -1.05
        offset = (self.y - (paddle.y + paddle.height / 2)) / (paddle.height / 2)
        self.vel_y += offset * settings.BALL_SPIN_FACTOR
        self._events.append(("hit", self.x, self.y, "right" if paddle.x > settings.SCREEN_WIDTH / 2 else "left", 1))