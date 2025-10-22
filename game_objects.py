# Archivo: game_objects.py - Pelota y paletas (dt, swept, spin, boost)
# ASCII puro

import cv2
import numpy as np
import time
import settings

_RNG = np.random.default_rng(int(time.time() * 1000) % (2**32))


class Ball:
    def __init__(self):
        self.radius = int(settings.BALL_RADIUS)
        self.color = settings.BALL_COLOR
        self.reset(direction=1)

    def _clamp_speed(self):
        speed = float(np.hypot(self.vx, self.vy))
        max_s = float(settings.BALL_MAX_SPEED)
        if speed > max_s:
            k = max_s / speed
            self.vx *= k
            self.vy *= k
        min_abs_vx = max(3.0, settings.BALL_MIN_SPEED * 0.5)
        if abs(self.vx) < min_abs_vx:
            self.vx = np.copysign(min_abs_vx, self.vx)

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        if self.y - self.radius <= 0:
            self.y = float(self.radius)
            self.vy = abs(self.vy)
        elif self.y + self.radius >= settings.SCREEN_HEIGHT:
            self.y = float(settings.SCREEN_HEIGHT - self.radius)
            self.vy = -abs(self.vy)
        self._clamp_speed()

    def draw(self, frame):
        cv2.circle(frame, (int(self.x), int(self.y)), self.radius, self.color, -1)

    def reset(self, direction=1):
        self.x = float(settings.SCREEN_WIDTH // 2)
        self.y = float(settings.SCREEN_HEIGHT // 2)
        base = float(settings.INITIAL_BALL_SPEED)
        ang = _RNG.uniform(-0.30, 0.30)
        self.vx = float(direction) * base * np.cos(ang)
        self.vy = base * np.sin(ang)
        self._clamp_speed()

    def _swept_hit(self, pad, dt):
        if self.vx == 0:
            return False
        f = float(settings.COLLISION_FORGIVENESS)
        if self.vx > 0:
            x_face = pad.x - self.radius - 0.5
        else:
            x_face = pad.x + pad.width + self.radius + 0.5
        t = (x_face - self.x) / (self.vx * dt)
        if t < 0.0 or t > 1.0:
            return False
        y_t = self.y + self.vy * dt * t
        if (y_t + self.radius > pad.y - f) and (y_t - self.radius < pad.y + pad.height + f):
            self.x = x_face
            self.y = y_t
            self.vx *= -1.0
            center = pad.y + pad.height / 2.0
            rel = (self.y - center) / max(1.0, pad.height / 2.0)
            rel = float(np.clip(rel, -1.0, 1.0))
            self.vy += rel * float(settings.BALL_SPIN_GAIN)
            self.vy += float(_RNG.uniform(-settings.BALL_NOISE_Y, settings.BALL_NOISE_Y))
            mult = 1.0 + float(settings.BALL_SPEED_HIT_BOOST)
            self.vx *= mult
            self.vy *= mult
            self._clamp_speed()
            return True
        return False

    def check_collisions(self, ai_paddle, player_paddle, dt=1 / 60.0):
        events = []
        pad = ai_paddle if self.vx < 0 else player_paddle
        side = "ai" if self.vx < 0 else "player"

        if self._swept_hit(pad, dt):
            events.append(("hit", float(self.x), float(self.y), side))
            if side == "player":
                self.x -= 1.0
            else:
                self.x += 1.0
            return events

        f = float(settings.COLLISION_FORGIVENESS)
        if (self.x + self.radius > pad.x - f and
            self.x - self.radius < pad.x + pad.width + f and
            self.y + self.radius > pad.y - f and
            self.y - self.radius < pad.y + pad.height + f):
            self.vx *= -1.0
            center = pad.y + pad.height / 2.0
            rel = (self.y - center) / max(1.0, pad.height / 2.0)
            rel = float(np.clip(rel, -1.0, 1.0))
            self.vy += rel * float(settings.BALL_SPIN_GAIN)
            self.vy += float(_RNG.uniform(-settings.BALL_NOISE_Y, settings.BALL_NOISE_Y))
            mult = 1.0 + float(settings.BALL_SPEED_HIT_BOOST)
            self.vx *= mult
            self.vy *= mult
            if side == "player":
                self.x = float(pad.x - self.radius - 1.0)
            else:
                self.x = float(pad.x + pad.width + self.radius + 1.0)
            self._clamp_speed()
            events.append(("hit", float(self.x), float(self.y), side))
        return events


class PlayerPaddle:
    def __init__(self, x_pos, color=(255, 255, 255)):
        self.x = float(x_pos)
        self.y = float(settings.SCREEN_HEIGHT // 2 - settings.PADDLE_HEIGHT // 2)
        self.width = int(settings.PADDLE_WIDTH)
        self.height = int(settings.PADDLE_HEIGHT)
        self.color = color

    def update(self, hand_y):
        target_y = float(hand_y - self.height // 2)
        self.y = float(np.clip(target_y, 0, settings.SCREEN_HEIGHT - self.height))

    def draw(self, frame):
        cv2.rectangle(frame, (int(self.x), int(self.y)),
                      (int(self.x + self.width), int(self.y + self.height)),
                      self.color, -1)


class AIPaddle(PlayerPaddle):
    def __init__(self, x_pos, color=(255, 255, 255)):
        super().__init__(x_pos, color)
        self.target_y = self.y
        self.react_gain = 1.0

    def update(self, ball, reactivity=0.02, boost=1.0, error_rate=0.2):
        desired = getattr(self, "target_y", float(ball.y))
        jitter = float(_RNG.uniform(-80.0, 80.0)) * float(error_rate)
        self.target_y = float(desired + jitter)
        max_step = float(settings.AI_PADDLE_MAX_SPEED) * float(max(0.5, min(1.5, boost)))
        self.react_gain = float(max(0.0, reactivity))
        dy = self.target_y - (self.y + self.height / 2.0)
        step = float(np.clip(dy * self.react_gain, -max_step, max_step))
        self.y = float(np.clip(self.y + step, 0, settings.SCREEN_HEIGHT - self.height))

    def get_last_target_y(self):
        return float(self.y + self.height / 2.0)