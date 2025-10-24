# game_objects.py - Paletas y pelota con colision barrida y perfiles (ASCII)

import math
import settings

def clamp(v, a, b):
    return max(a, min(b, v))

class PaddleBase:
    def __init__(self, x, color):
        self.x = int(x)
        self.y = 0
        self.width = settings.PADDLE_WIDTH
        self.height = settings.PADDLE_HEIGHT
        self.color = color
        self.max_speed = settings.PADDLE_MAX_SPEED

    def center_y(self):
        return self.y + self.height * 0.5

    def update(self, target_y, dt):
        """Movimiento suave con zona muerta para evitar tiriteo."""
        if target_y is None:
            return
        # alinear el centro de la paleta con target_y
        target_top = int(target_y - self.height * 0.5)
        dy = target_top - self.y

        # zona muerta
        DEADZONE = 5
        if abs(dy) <= DEADZONE:
            return

        # control proporcional suave con limite de velocidad
        k = 8.0  # ganancia
        desired_step = int(k * dy * dt * self.max_speed / 300.0)
        max_step = int(self.max_speed * dt)
        step = clamp(desired_step, -max_step, max_step)

        self.y += step
        self.y = clamp(self.y, 0, settings.SCREEN_HEIGHT - self.height)

class PlayerPaddle(PaddleBase):
    pass

class AIPaddle(PaddleBase):
    pass

class Ball:
    def __init__(self):
        # posiciones previas para colision barrida
        self.last_x = 0.0
        self.last_y = 0.0
        # parametros del perfil activo (se actualizan en reset/apply_profile_change)
        self.spd_start = settings.BALL_PROFILES[settings.BALL_PROFILE]["start"]
        self.spd_max   = settings.BALL_PROFILES[settings.BALL_PROFILE]["max"]
        self.spd_step  = settings.BALL_PROFILES[settings.BALL_PROFILE]["step"]
        self.reset(direction=1)

    def reset(self, direction=1):
        # tomar perfil actual
        perfil = settings.BALL_PROFILES[settings.BALL_PROFILE]
        self.spd_start = perfil["start"]
        self.spd_max   = perfil["max"]
        self.spd_step  = perfil["step"]

        # centrar pelota
        self.x = settings.SCREEN_WIDTH // 2
        self.y = settings.SCREEN_HEIGHT // 2
        self.last_x = float(self.x)
        self.last_y = float(self.y)

        # direccion inicial con angulo leve aleatorio
        import random
        ang_deg = random.uniform(-25, 25)
        ang = math.radians(ang_deg)
        spd = self.spd_start
        self.vx = direction * spd * math.cos(ang)
        self.vy = spd * math.sin(ang)
        self._cap_min_vy()

    def _cap_min_vy(self):
        if abs(self.vy) < settings.BALL_MIN_VY:
            self.vy = settings.BALL_MIN_VY if self.vy >= 0 else -settings.BALL_MIN_VY

    def apply_profile_change(self):
        """Se llama cuando el usuario cambia el perfil (1/2/3) en caliente."""
        perfil = settings.BALL_PROFILES[settings.BALL_PROFILE]
        self.spd_max  = perfil["max"]
        self.spd_step = perfil["step"]
        # no tocamos vx/vy ni spd_start hasta el proximo reset

    def update(self, dt):
        # guardar posicion anterior
        self.last_x = float(self.x)
        self.last_y = float(self.y)

        # integrar
        self.x += self.vx * dt
        self.y += self.vy * dt

        # rebotes contra techo y suelo
        top = settings.BALL_RADIUS
        bot = settings.SCREEN_HEIGHT - settings.BALL_RADIUS
        if self.y <= top:
            self.y = top
            self.vy *= -1
        elif self.y >= bot:
            self.y = bot
            self.vy *= -1

    def _bounce_angle(self, paddle_center_y):
        # calcula angulo de salida segun punto de impacto en la paleta
        rel = (self.y - paddle_center_y) / (settings.PADDLE_HEIGHT * 0.5)
        rel = clamp(rel, -1.0, 1.0)
        max_ang = math.radians(settings.BALL_MAX_BOUNCE_DEG)
        return rel * max_ang

    def check_collisions(self, ai_paddle, player_paddle):
        """
        Colisiones barridas contra los planos verticales de las paletas.
        Evita que la pelota atraviese cuando va rapido o el dt es grande.
        """
        events = []
        r = settings.BALL_RADIUS

        # --- Paleta IA (izquierda): plano x = ai.right ---
        ax, ay, aw, ah = ai_paddle.x, ai_paddle.y, ai_paddle.width, ai_paddle.height
        ai_plane = ax + aw
        if self.vx < 0:
            # ¿cruzo el borde derecho de la paleta IA?
            if (self.last_x - r) >= ai_plane and (self.x - r) <= ai_plane:
                denom = (self.x - r) - (self.last_x - r)
                t = 0.0 if denom == 0 else (ai_plane - (self.last_x - r)) / denom
                t = clamp(t, 0.0, 1.0)
                impact_y = self.last_y + (self.y - self.last_y) * t
                if ay <= impact_y <= ay + ah:
                    # colocar al contacto y rebotar
                    self.x = ai_plane + r
                    ang = self._bounce_angle(ai_paddle.center_y())
                    spd = (self.vx ** 2 + self.vy ** 2) ** 0.5
                    spd = min(spd + self.spd_step, self.spd_max)
                    self.vx = abs(spd * math.cos(ang))
                    self.vy = spd * math.sin(ang)
                    self._cap_min_vy()
                    events.append(("hit", self.x, impact_y, "left"))

        # --- Paleta Jugador (derecha): plano x = player.left ---
        px, py, pw, ph = player_paddle.x, player_paddle.y, player_paddle.width, player_paddle.height
        pl_plane = px
        if self.vx > 0:
            # ¿cruzo el borde izquierdo de la paleta del jugador?
            if (self.last_x + r) <= pl_plane and (self.x + r) >= pl_plane:
                denom = (self.x + r) - (self.last_x + r)
                t = 0.0 if denom == 0 else (pl_plane - (self.last_x + r)) / denom
                t = clamp(t, 0.0, 1.0)
                impact_y = self.last_y + (self.y - self.last_y) * t
                if py <= impact_y <= py + ph:
                    self.x = pl_plane - r
                    ang = self._bounce_angle(player_paddle.center_y())
                    spd = (self.vx ** 2 + self.vy ** 2) ** 0.5
                    spd = min(spd + self.spd_step, self.spd_max)
                    self.vx = -abs(spd * math.cos(ang))
                    self.vy = spd * math.sin(ang)
                    self._cap_min_vy()
                    events.append(("hit", self.x, impact_y, "right"))

        return events