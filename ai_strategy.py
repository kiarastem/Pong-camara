# ai_strategy.py - IA con prediccion, aprendizaje y habilidad inicial baja (ASCII)

import math
import random
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
    IA educativa:
      - Con vx<0 predice el cruce y apunta al objetivo.
      - Tiene habilidad inicial baja (skill), que mejora con la exactitud reciente.
      - Introduce sesgo al centro y ruido cuando la skill es baja (mas "tonta").
    Panel expone: pred_y, target_y, error_pct, acc_recent, skill.
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

        # habilidad inicial (mas baja = mas errores)
        self.skill = float(getattr(settings, "AI_SKILL_START", 0.35))

    def _bin_index(self, y, h):
        y = clamp(int(y), 0, h - 1)
        band_h = h / float(self.bins)
        idx = int(y // band_h)
        return clamp(idx, 0, self.bins - 1)

    def _apply_dumbness(self, base_target, h):
        """
        Mezcla con centro y agrega ruido segun skill:
        - skill baja -> mas sesgo al centro y mas ruido.
        """
        center = h * 0.5
        bias = (1.0 - self.skill)  # 0..1
        noisy = base_target * (1.0 - bias) + center * bias
        # ruido proporcional a pantalla
        amp = bias * (h * 0.12)
        noisy += random.uniform(-amp, amp)
        # suavizado simple
        if self.target_y is None:
            return noisy
        alpha = 0.35 + 0.45 * self.skill  # mas skill -> reacciona mas rapido
        return (1.0 - alpha) * float(self.target_y) + alpha * float(noisy)

    def decide(self, ball, ai_center_y, dt):
        w = settings.SCREEN_WIDTH
        h = settings.SCREEN_HEIGHT
        r = settings.BALL_RADIUS
        vx = float(getattr(ball, "vx", 0.0))
        vy = float(getattr(ball, "vy", 0.0))

        if vx < 0:
            x_target = self.x_ai + settings.PADDLE_WIDTH
            self.pred_y = predict_ball_y_at_x(x_target, ball.x, ball.y, vx, vy, w, h, r)
            base_target = h * 0.5 if self.pred_y is None else float(self.pred_y)

            # sesgo a zonas debiles (opcional, leve)
            if sum(self.weak_counts) > 0:
                worst_idx = max(range(self.bins), key=lambda i: self.weak_counts[i])
                band_h = h / float(self.bins)
                weak_center = (worst_idx + 0.5) * band_h
                base_target = (1.0 - self.learn_rate) * base_target + self.learn_rate * weak_center

            # aplicar "torpeza" segun skill
            self.target_y = self._apply_dumbness(base_target, h)
        else:
            self.pred_y = None
            self.target_y = h * 0.5

        # error relativo vs prediccion
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

        # skill sube con la exactitud (limites 0.2..0.95)
        tgt_skill = 0.2 + 0.75 * (self.acc_recent / 100.0)
        # suavizado para no saltar bruscamente
        self.skill = clamp(0.85 * self.skill + 0.15 * tgt_skill, 0.2, 0.95)