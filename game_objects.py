# game_objects.py
# Paletas y pelota con fisicas mejoradas (ASCII)
# - Velocidades en px/seg, integradas por dt
# - Aceleracion en golpes y tope por BALL_MAX_SPEED
# - Rebote con angulo segun punto de impacto en paleta
# - Spin vertical (segun desplazamiento relativo)
# - CCD ligera: barrido por el eje X hacia paletas, evita atravesar
# - Eventos ("hit", x, y, "left"/"right", potencia) para FX

import math
import random
import settings


# ---------------- util ----------------

def clamp(v, a, b):
    return max(a, min(b, v))


# ---------------- Paletas ----------------

class _BasePaddle:
    def __init__(self, x, color):
        self.x = int(x)
        self.y = int(settings.SCREEN_HEIGHT // 2 - settings.PADDLE_HEIGHT // 2)
        self.width = int(settings.PADDLE_WIDTH)
        self.height = int(settings.PADDLE_HEIGHT)
        self.color = color
        self.max_speed = 900.0  # px/seg, se siente fluido con camara

    def rect(self):
        return self.x, self.y, self.width, self.height

    def center_y(self):
        return self.y + self.height * 0.5

    def _move_to(self, target_y, dt):
        if target_y is None:
            return
        target = int(target_y - self.height * 0.5)
        dy = target - self.y
        max_step = int(self.max_speed * dt)
        if abs(dy) > max_step:
            dy = max_step if dy > 0 else -max_step
        self.y += dy
        self.y = int(clamp(self.y, 0, settings.SCREEN_HEIGHT - self.height))


class PlayerPaddle(_BasePaddle):
    def update(self, y_px, dt):
        self._move_to(y_px, dt)


class AIPaddle(_BasePaddle):
    def update(self, target_y, dt):
        # IA siempre usa el mismo limitador de velocidad para no ser imposible
        self._move_to(target_y, dt)


# ---------------- Pelota ----------------

class Ball:
    def __init__(self):
        self.radius = int(settings.BALL_RADIUS)
        self.reset(direction=1)

    def reset(self, direction=1):
        self.x = float(settings.SCREEN_WIDTH * 0.5)
        self.y = float(settings.SCREEN_HEIGHT * 0.5)
        # velocidad base desde settings (px/seg)
        base = float(getattr(settings, "BALL_BASE_SPEED", 900.0))
        ang = random.uniform(-0.35, 0.35)  # angulo inicial leve
        self.vx = base * (1 if direction >= 0 else -1) * math.cos(ang)
        self.vy = base * math.sin(ang)
        self._events = []

    # ---------- integracion ----------
    def update(self, dt):
        # integracion simple
        self.x += self.vx * dt
        self.y += self.vy * dt

        # paredes arriba/abajo
        r = self.radius
        if self.y < r:
            self.y = r
            self.vy = -self.vy
        elif self.y > settings.SCREEN_HEIGHT - r:
            self.y = settings.SCREEN_HEIGHT - r
            self.vy = -self.vy

    # ---------- colisiones ----------
    def check_collisions(self, paddle_l: AIPaddle, paddle_r: PlayerPaddle):
        """Devuelve eventos de golpe para FX. Tambien resuelve rebotes y aceleracion."""
        self._events.clear()
        # hasta dos intentos por frame por seguridad
        for _ in range(2):
            if self._swept_vs_paddle(paddle_l, is_left=True):
                continue
            if self._swept_vs_paddle(paddle_r, is_left=False):
                continue
            break
        return list(self._events)

    def _swept_vs_paddle(self, paddle, is_left: bool) -> bool:
        """CCD ligera por eje X:
        - Si la velocidad en X acerca la pelota a la paleta y el segmento cruza el rectangulo,
          fijamos posicion de impacto, rebotamos y aplicamos spin/aceleracion."""
        r = self.radius
        px, py, pw, ph = paddle.rect()

        # sentido hacia la paleta
        moving_left = self.vx < 0
        if is_left and not moving_left:
            return False
        if (not is_left) and moving_left:
            return False

        # proyeccion de la trayectoria en X hasta el borde de la paleta
        next_x = self.x + self.vx * (1/60.0)  # estimacion corta para detectar penetraciones rapidas
        if is_left:
            impact_x = px + pw + r
            if next_x + r < impact_x:
                return False
        else:
            impact_x = px - r
            if next_x - r > impact_x:
                return False

        # comprobar solape vertical si en el rango cercano al borde
        # usamos la posicion actual de la pelota
        if (self.y + r) < py or (self.y - r) > (py + ph):
            return False

        # colocar la pelota justo al borde y reflejar vx
        self.x = float(impact_x)
        self.vx = -self.vx

        # calcular desplazamiento relativo de impacto (para angulo/spin)
        pad_cy = paddle.center_y()
        rel = (self.y - pad_cy) / (ph * 0.5)          # -1..1
        rel = clamp(rel, -1.0, 1.0)

        # spin: ajusta vy segun el punto de contacto
        spin = rel * 420.0
        self.vy += spin

        # asegurar que no quede casi horizontal
        min_vy = 140.0
        if 0 <= self.vy < min_vy:
            self.vy = min_vy
        elif -min_vy < self.vy < 0:
            self.vy = -min_vy

        # acelerar tras golpe con limite
        accel = float(getattr(settings, "BALL_ACCEL", 1.10))
        max_speed = float(getattr(settings, "BALL_MAX_SPEED", 1600.0))
        self._set_speed(min(self._speed() * accel, max_speed))

        # registrar evento para FX
        side = "left" if is_left else "right"
        potencia = self._speed() / max_speed
        self._events.append(("hit", int(self.x), int(self.y), side, float(potencia)))
        return True

    # ---------- auxiliares ----------
    def _speed(self):
        return math.hypot(self.vx, self.vy)

    def _set_speed(self, s):
        sp = self._speed()
        if sp <= 1e-5:
            return
        k = s / sp
        self.vx *= k
        self.vy *= k