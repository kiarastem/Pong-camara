# Archivo: game_objects.py
# Logica principal de objetos del juego (pelota, paletas, colisiones)
# ASCII puro

import cv2
import numpy as np
import settings


# ---------- Clase de la pelota ----------
class Ball:
    def __init__(self):
        self.radius = settings.BALL_RADIUS
        self.color = settings.BALL_COLOR
        self.reset()

    def reset(self, direction=1):
        """Reinicia la pelota al centro con direccion inicial."""
        self.x = settings.SCREEN_WIDTH / 2
        self.y = settings.SCREEN_HEIGHT / 2
        self.vx = direction * settings.BALL_SPEED_X
        self.vy = np.random.choice([-1, 1]) * settings.BALL_SPEED_Y
        self.speed = settings.BALL_BASE_SPEED

    def update(self, dt):
        """Actualiza posicion y velocidad con rebotes verticales."""
        self.x += self.vx * dt
        self.y += self.vy * dt

        if self.y - self.radius <= 0 or self.y + self.radius >= settings.SCREEN_HEIGHT:
            self.vy = -self.vy
            self.y = np.clip(self.y, self.radius, settings.SCREEN_HEIGHT - self.radius)

        # aumenta velocidad gradualmente (no exponencial)
        self.speed = min(self.speed * (1.0 + settings.BALL_SPEED_INC * dt), settings.BALL_SPEED_MAX)
        self.vx = np.sign(self.vx) * self.speed
        self.vy = np.sign(self.vy) * (abs(self.vy) / max(abs(self.vx), 1)) * self.speed

    def check_collisions(self, ai_paddle, player_paddle, dt):
        """Detecta colisiones con paletas y genera eventos."""
        events = []
        # Paleta izquierda (IA)
        if (
            self.vx < 0
            and ai_paddle.x < self.x - self.radius < ai_paddle.x + ai_paddle.width
            and ai_paddle.y < self.y < ai_paddle.y + ai_paddle.height
        ):
            self.vx = -self.vx
            self.x = ai_paddle.x + ai_paddle.width + self.radius
            events.append(("hit", self.x, self.y, "ai"))

        # Paleta derecha (Jugador)
        elif (
            self.vx > 0
            and player_paddle.x < self.x + self.radius < player_paddle.x + player_paddle.width
            and player_paddle.y < self.y < player_paddle.y + player_paddle.height
        ):
            self.vx = -self.vx
            self.x = player_paddle.x - self.radius
            events.append(("hit", self.x, self.y, "player"))

        return events

    def draw(self, frame):
        cv2.circle(frame, (int(self.x), int(self.y)), self.radius, self.color, -1)


# ---------- Clase base de paleta ----------
class Paddle:
    def __init__(self, x_pos, color=(255, 255, 255)):
        self.width = settings.PADDLE_WIDTH
        self.height = settings.PADDLE_HEIGHT
        self.x = x_pos
        self.y = settings.SCREEN_HEIGHT / 2 - self.height / 2
        self.v = 0.0
        self.color = color

    def draw(self, frame):
        cv2.rectangle(
            frame,
            (int(self.x), int(self.y)),
            (int(self.x + self.width), int(self.y + self.height)),
            self.color,
            -1,
        )


# ---------- Paleta del jugador ----------
class PlayerPaddle(Paddle):
    def update(self, y_hand):
        """Actualiza la posicion segun la mano detectada."""
        target_y = y_hand - self.height / 2
        self.y += (target_y - self.y) * 0.3
        self.y = np.clip(self.y, 0, settings.SCREEN_HEIGHT - self.height)


# ---------- Paleta de la IA ----------
class AIPaddle(Paddle):
    def __init__(self, x_pos, color=(255, 0, 0)):
        super().__init__(x_pos, color)
        self.target_y = self.y

    def update(self, ball, reactivity=0.03, boost=1.0, error_rate=0.2, dt=1 / 60.0):
        """
        Control PD 'humano':
        - Deadband para evitar oscilaciones cerca del objetivo.
        - Limite de aceleracion (inercia).
        - Velocidad max dependiente de la bola.
        - Leve sobrepaso al corregir errores grandes.
        """
        desired = getattr(self, "target_y", float(ball.y))
        desired = float(np.clip(desired, 0.0, float(settings.SCREEN_HEIGHT)))

        max_speed_base = float(settings.AI_PADDLE_MAX_SPEED)
        speed_scale = 0.90 + 0.60 * float(np.clip(abs(ball.vx) / 900.0, 0.0, 1.0))
        max_speed = max_speed_base * speed_scale * float(max(0.6, min(1.7, boost)))
        max_accel = float(getattr(settings, "AI_MAX_ACCEL", 4800.0))

        kp = float(reactivity * 2.0)
        kd = float(getattr(settings, "AI_D_GAIN", 0.22))
        dead = float(getattr(settings, "AI_DEADBAND_PX", 10.0))

        center = self.y + self.height / 2.0
        err = desired - center
        if abs(err) > 120.0:
            desired += np.sign(err) * 12.0

        if abs(err) < dead:
            target_v = 0.0
        else:
            target_v = kp * err - kd * self.v
            target_v = float(np.clip(target_v, -max_speed, max_speed))

        if dt > 0:
            a_cmd = (target_v - self.v) / dt
            a_cmd = float(np.clip(a_cmd, -max_accel, max_accel))
            self.v += a_cmd * dt

        self.y += self.v * dt

        if self.y <= 0.0:
            self.y = 0.0
            self.v = 0.0
        elif self.y >= settings.SCREEN_HEIGHT - self.height:
            self.y = float(settings.SCREEN_HEIGHT - self.height)
            self.v = 0.0