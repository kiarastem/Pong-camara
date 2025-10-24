# ai_strategy.py - IA con prediccion, aprendizaje y suavizado anti-tiriteo (ASCII)

import math
import random
import time
import settings

def clamp(v, a, b):
    return max(a, min(b, v))

def reflect_y_at_walls(y, h, r):
    top = r
    bot = h - r
    if bot <= top:
        return clamp(int(y), 0, h - 1)
    span = bot - top
    rel = (y - top) % (2 * span)
    if rel > span:
        rel = 2 * span - rel
    return int(top + rel)

def predict_ball_y_at_x(x_target, x0, y0, vx, vy, w, h, r):
    if vx == 0:
        return None
    t = (x_target - x0) / vx
    if t <= 0:
        return None
    return reflect_y_at_walls(y0 + vy * t, h, r)

class OpponentAI:
    """
    IA educativa suave:
      - Predice cruce cuando vx<0 y aplica filtros EMA para evitar saltos.
      - "Torpeza" controlada por skill: sesgo al centro + ruido estable (no por frame).
      - Aprende con exactitud reciente y sube la skill de a poco.
    Panel: pred_y, target_y, error_pct, acc_recent, skill.
    """
    def __init__(self, x_ai):
        self.x_ai = x_ai
        self.pred_y = None
        self.target_y = None
        self.error_pct = 0.0

        # aprendizaje por bandas
        self.bins = int(getattr(settings, "AI_LEARN_BINS", 6))
        self.weak_counts = [0 for _ in range(self.bins)]
        self.learn_rate = float(getattr(settings, "AI_LEARN_RATE", 0.15))
        self.hist_window = int(getattr(settings, "AI_HISTORY", 12))
        self._recent_covers = []  # 1 cubre, 0 falla
        self.acc_recent = 0.0

        # habilidad
        self.skill = float(getattr(settings, "AI_SKILL_START", 0.35))

        # suavizado y ruido estable
        self.pred_ema = None
        self.target_ema = None
        self._noise = 0.0
        self._noise_t = 0.0
        self.noise_period = 0.25  # s

    def _bin_index(self, y, h):
        y = clamp(int(y), 0, h - 1)
        band_h = h / float(self.bins)
        idx = int(y // band_h)
        return clamp(idx, 0, self.bins - 1)

    def _update_noise(self, h):
        now = time.time()
        if (now - self._noise_t) >= self.noise_period:
            bias = (1.0 - self.skill)  # 0..1 mas bajo => mas ruido
            amp = bias * (h * 0.08)
            self._noise = random.uniform(-amp, amp)
            self._noise_t = now

    def decide(self, ball, ai_center_y, dt):
        w = settings.SCREEN_WIDTH
        h = settings.SCREEN_HEIGHT
        r = settings.BALL_RADIUS
        vx = float(getattr(ball, "vx", 0.0))
        vy = float(getattr(ball, "vy", 0.0))

        # actualizar ruido estable
        self._update_noise(h)

        if vx < 0:
            # prediccion bruta
            x_target = self.x_ai + settings.PADDLE_WIDTH
            pred_raw = predict_ball_y_at_x(x_target, ball.x, ball.y, vx, vy, w, h, r)
            if pred_raw is None:
                pred_raw = h * 0.5

            # EMA en prediccion segun skill (mas skill => responde mas rapido)
            alpha_pred = 0.25 + 0.5 * self.skill  # 0.25..0.75
            if self.pred_ema is None:
                self.pred_ema = float(pred_raw)
            else:
                self.pred_ema = (1.0 - alpha_pred) * self.pred_ema + alpha_pred * float(pred_raw)
            self.pred_y = self.pred_ema

            # sesgo leve a la zona debil
            base_target = float(self.pred_y)
            if sum(self.weak_counts) > 0:
                worst_idx = max(range(self.bins), key=lambda i: self.weak_counts[i])
                band_h = h / float(self.bins)
                weak_center = (worst_idx + 0.5) * band_h
                base_target = (1.0 - self.learn_rate) * base_target + self.learn_rate * weak_center

            # "torpeza": mezcla al centro + ruido estable (no cambia por frame)
            center = h * 0.5
            bias = (1.0 - self.skill)
            mixed = base_target * (1.0 - 0.5 * bias) + center * (0.5 * bias) + self._noise

            # EMA final del objetivo para suavizar
            alpha_tgt = 0.30 + 0.50 * self.skill  # 0.30..0.80
            if self.target_ema is None:
                self.target_ema = float(mixed)
            else:
                self.target_ema = (1.0 - alpha_tgt) * self.target_ema + alpha_tgt * float(mixed)

            self.target_y = clamp(self.target_ema, r, h - r)
        else:
            # alejandose: volver al centro, suavizado
            center = h * 0.5
            alpha_back = 0.2
            if self.target_ema is None:
                self.target_ema = center
            else:
                self.target_ema = (1.0 - alpha_back) * self.target_ema + alpha_back * center
            self.target_y = self.target_ema
            self.pred_y = None

        # error relativo vs prediccion suavizada
        if self.pred_y is not None:
            err = abs(ai_center_y - self.pred_y)
            self.error_pct = clamp(err / (settings.PADDLE_HEIGHT * 0.5), 0.0, 2.0) * 100.0
        else:
            self.error_pct = 0.0

        return self.target_y

    def learn_on_point_end(self, player_scored: bool, ball_final_y: float):
        """Actualiza aprendizaje, exactitud y skill al terminar cada punto."""
        h = settings.SCREEN_HEIGHT
        if ball_final_y is None:
            return

        came_to_ai = bool(player_scored)  # si anoto el jugador, fue al lado IA

        if came_to_ai:
            self._recent_covers.append(0)
            idx = self._bin_index(ball_final_y, h)
            self.weak_counts[idx] += 1
        else:
            self._recent_covers.append(1)

        if len(self._recent_covers) > self.hist_window:
            self._recent_covers.pop(0)

        # exactitud reciente
        if self._recent_covers:
            self.acc_recent = sum(self._recent_covers) / float(len(self._recent_covers)) * 100.0
        else:
            self.acc_recent = 0.0

        # skill sube con la exactitud (limites 0.25..0.95), suave
        tgt_skill = 0.25 + 0.70 * (self.acc_recent / 100.0)
        self.skill = clamp(0.90 * self.skill + 0.10 * tgt_skill, 0.25, 0.95)