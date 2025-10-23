# Archivo: game_objects.py
# Logica de objetos (pelota, paletas, colisiones)
# ASCII puro

import cv2
import numpy as np
import time
import settings


# ---------- Pelota ----------
class Ball:
    def __init__(self):
        self.radius = settings.BALL_RADIUS
        self.color = settings.BALL_COLOR
        # use a Generator for reproducible, modern random API
        seed = int(time.time() * 1000) % (2**32)
        self._rng = np.random.default_rng(seed)
        self.reset(direction=1)

    def reset(self, direction=1):
        self.x = settings.SCREEN_WIDTH / 2.0
        self.y = settings.SCREEN_HEIGHT / 2.0
        # initialize base speed and direction-consistent velocity components
        self.speed = settings.BALL_BASE_SPEED
        dir_x = float(direction)
        # pick vertical sign randomly
        dir_y = float(self._rng.choice([-1.0, 1.0]))
        # start with a velocity proportional to speed but respecting configured base components
        # keep initial vx/vy proportional to settings' base speeds but scale to match self.speed
        base_vx = abs(settings.BALL_SPEED_X)
        base_vy = abs(settings.BALL_SPEED_Y)
        # avoid division by zero
        if base_vx <= 0 and base_vy <= 0:
            self.vx = dir_x * self.speed
            self.vy = dir_y * 0.0
        else:
            # compute ratio and set vx/vy so that hypot(vx,vy) approximates self.speed
            ratio = base_vy / max(base_vx, 1.0)
            vy = min(settings.BALL_SPIN_CLAMP, self.speed * (ratio / (1.0 + ratio)))
            vx = max(1e-3, np.sqrt(max(0.0, self.speed * self.speed - vy * vy)))
            self.vx = dir_x * vx
            self.vy = dir_y * vy

    def update(self, dt):
        dt = max(0.0, float(dt))
        self.x += self.vx * dt
        self.y += self.vy * dt

        # rebote vertical
        if self.y - self.radius <= 0.0:
            self.y = self.radius
            self.vy = abs(self.vy)
        elif self.y + self.radius >= settings.SCREEN_HEIGHT:
            self.y = settings.SCREEN_HEIGHT - self.radius
            self.vy = -abs(self.vy)

    def _apply_spin(self, paddle, contact_y):
        rel = ((contact_y - (paddle.y + paddle.height / 2.0)) / (paddle.height / 2.0))
        rel = np.clip(rel, -1.0, 1.0)
        spin = rel * settings.BALL_SPIN_FACTOR
        self.vy = float(np.clip(self.vy + spin, -settings.BALL_SPIN_CLAMP, settings.BALL_SPIN_CLAMP))

    def check_collisions(self, ai_paddle, player_paddle):
        events = []

        # colision con paleta IA (izquierda)
        if self.vx < 0:
            p = ai_paddle
            if (p.x <= self.x - self.radius <= p.x + p.width) and (p.y <= self.y <= p.y + p.height):
                # reposition outside paddle to avoid double-collision
                self.x = p.x + p.width + self.radius
                # increase speed on hit (discrete increment)
                self.speed = min(settings.BALL_SPEED_MAX, self.speed + settings.BALL_SPEED_INC)
                # apply spin based on contact point
                self._apply_spin(p, self.y)
                # recompute velocity components preserving direction and proportionality
                dir_x = 1.0
                vy_ratio = np.clip(abs(self.vy) / max(abs(self.vx), 1.0), 0.35, 2.0)
                self.vx = dir_x * self.speed
                self.vy = np.sign(self.vy) * min(settings.BALL_SPIN_CLAMP, self.speed * vy_ratio)
                events.append(("hit", self.x, self.y, "ai"))

        # colision con paleta Jugador (derecha)
        if self.vx > 0:
            p = player_paddle
            if (p.x <= self.x + self.radius <= p.x + p.width) and (p.y <= self.y <= p.y + p.height):
                # reposition outside paddle to avoid double-collision
                self.x = p.x - self.radius
                # increase speed on hit
                self.speed = min(settings.BALL_SPEED_MAX, self.speed + settings.BALL_SPEED_INC)
                # apply spin
                self._apply_spin(p, self.y)
                dir_x = -1.0
                vy_ratio = np.clip(abs(self.vy) / max(abs(self.vx), 1.0), 0.35, 2.0)
                self.vx = dir_x * self.speed
                self.vy = np.sign(self.vy) * min(settings.BALL_SPIN_CLAMP, self.speed * vy_ratio)
                events.append(("hit", self.x, self.y, "player"))

        return events

    def draw(self, frame):
        cv2.circle(frame, (int(self.x), int(self.y)), self.radius, self.color, -1)


# ---------- Clase base Paleta ----------
class Paddle:
    def __init__(self, x_pos, color=(255, 255, 255)):
        self.width = settings.PADDLE_WIDTH
        self.height = settings.PADDLE_HEIGHT
        self.x = float(x_pos)
        self.y = settings.SCREEN_HEIGHT / 2.0 - self.height / 2.0
        self.v = 0.0
        self.color = color

    def clamp(self):
        if self.y < 0.0:
            self.y = 0.0
            self.v = 0.0
        max_y = settings.SCREEN_HEIGHT - self.height
        if self.y > max_y:
            self.y = max_y
            self.v = 0.0

    def draw(self, frame):
        cv2.rectangle(
            frame,
            (int(self.x), int(self.y)),
            (int(self.x + self.width), int(self.y + self.height)),
            self.color,
            -1,
        )


# ---------- Paleta Jugador ----------
class PlayerPaddle(Paddle):
    def update(self, y_hand):
        if y_hand is None:
            return
        target = float(y_hand) - self.height / 2.0
        alpha = float(np.clip(settings.PLAYER_FOLLOW_ALPHA, 0.0, 1.0))
        self.y += (target - self.y) * alpha
        self.clamp()


# ---------- Paleta IA ----------
class AIPaddle(Paddle):
    def __init__(self, x_pos, color=(255, 0, 0)):
        super().__init__(x_pos, color)
        self.target_y = self.y

    def update(self, reactivity, target_y, dt, ball_speed):
        target = float(np.clip(target_y - self.height / 2.0, 0.0, settings.SCREEN_HEIGHT - self.height))
        center = self.y
        err = target - center

        dead = float(getattr(settings, "AI_DEADBAND_PX", 12.0))
        kd = float(getattr(settings, "AI_D_GAIN", 0.19))
        kp = float(reactivity)
        if abs(err) < dead:
            desired_v = 0.0
        else:
            desired_v = kp * err - kd * self.v

        speed_factor = 0.85 + 0.6 * np.clip(ball_speed / 900.0, 0.0, 1.0)
        max_speed = float(settings.AI_PADDLE_MAX_SPEED) * speed_factor
        desired_v = float(np.clip(desired_v, -max_speed, max_speed))

        max_accel = float(getattr(settings, "AI_MAX_ACCEL", 4300.0))
        if dt > 0:
            a_cmd = (desired_v - self.v) / dt
            a_cmd = float(np.clip(a_cmd, -max_accel, max_accel))
            self.v += a_cmd * dt

        # small nudge: if error is large but velocity is nearly zero, help break static friction
        if abs(err) > dead and abs(self.v) < 20.0:
            # add a small velocity in px/s (not scaled by dt)
            nudge_v = np.sign(err) * min(0.08 * max_speed, 300.0)
            self.v += nudge_v

        self.y += self.v * dt
        self.clamp()