# game_objects.py
# Paletas y pelota (ASCII). Colisiones estilo Pong, ritmo agil para feria.

import settings
import math
import random

class BasePaddle:
    def __init__(self, x, color):
        self.x = int(x)
        self.y = settings.SCREEN_HEIGHT // 2
        self.width = int(settings.PADDLE_WIDTH)
        self.height = int(settings.PADDLE_HEIGHT)
        self.color = color
        self.speed = 900.0  # px/s para seguir targets rapidos

    def rect(self):
        return (self.x, self.y - self.height // 2, self.width, self.height)

    def clamp(self):
        half = self.height // 2
        self.y = max(half, min(settings.SCREEN_HEIGHT - half, self.y))

    def update_to(self, target_y, dt):
        if target_y is None:
            return
        diff = float(target_y) - float(self.y)
        step = self.speed * dt
        if abs(diff) <= step:
            self.y = int(target_y)
        else:
            self.y += int(step if diff > 0 else -step)
        self.clamp()

class PlayerPaddle(BasePaddle):
    def update(self, y_px, dt):
        self.update_to(y_px, dt)

class AIPaddle(BasePaddle):
    def update(self, target_y, dt):
        self.update_to(target_y, dt)

class Ball:
    def __init__(self):
        self.reset(direction=1)

    def reset(self, direction=1):
        self.x = float(settings.SCREEN_WIDTH // 2)
        self.y = float(settings.SCREEN_HEIGHT // 2)
        base = float(settings.BALL_BASE_SPEED)
        ang = random.uniform(-0.35, 0.35)
        self.vx = direction * base * math.cos(ang)
        self.vy = base * 0.55 * math.sin(ang)

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt

        # Rebote en techo/suelo
        top = settings.BALL_RADIUS
        bot = settings.SCREEN_HEIGHT - settings.BALL_RADIUS
        if self.y <= top:
            self.y = top
            self.vy = -self.vy
        elif self.y >= bot:
            self.y = bot
            self.vy = -self.vy

        # Clamp seguridad
        sp = abs(self.vx) + abs(self.vy)
        maxs = float(settings.BALL_MAX_SPEED)
        if sp > maxs:
            k = float(settings.BALL_SPEED_LIMIT)
            self.vx *= k
            self.vy *= k

    def _hit_paddle(self, pad_center_y):
        # invert X y anadir spin por offset
        self.vx = -self.vx * settings.BALL_ACCEL
        offset = (self.y - pad_center_y) / (settings.PADDLE_HEIGHT * 0.5)  # -1..1
        self.vy += offset * 180.0
        # clamp y
        maxvy = settings.BALL_MAX_SPEED * 0.75
        if abs(self.vy) > maxvy:
            self.vy = maxvy if self.vy > 0 else -maxvy

    def check_collisions(self, left_paddle, right_paddle):
        events = []
        # Paleta izquierda (IA)
        lx, ly, lw, lh = left_paddle.rect()
        if (self.x - settings.BALL_RADIUS) <= (lx + lw):
            if ly <= self.y <= (ly + lh):
                self.x = float(lx + lw + settings.BALL_RADIUS)
                self._hit_paddle(left_paddle.y)
                events.append(("hit", int(self.x), int(self.y), "left", 1))

        # Paleta derecha (Jugador)
        rx, ry, rw, rh = right_paddle.rect()
        if (self.x + settings.BALL_RADIUS) >= rx:
            if ry <= self.y <= (ry + rh):
                self.x = float(rx - settings.BALL_RADIUS)
                self._hit_paddle(right_paddle.y)
                events.append(("hit", int(self.x), int(self.y), "right", 1))
        return events