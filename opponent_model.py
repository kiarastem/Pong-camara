# opponent_model.py
# IA predictiva educativa (ASCII) con zona debil vertical simple

import random
import numpy as np
import settings

def _clamp(v, a, b):
    return max(a, min(b, v))

def _fold_axis(pos, low, high):
    # Plegado entre low y high para simular rebotes previos
    span = high - low
    if span <= 0:
        return _clamp(pos, low, high)
    u = (pos - low) % (2.0 * span)
    if u > span:
        u = 2.0 * span - u
    return low + u

class OpponentModelAdvanced:
    """
    Predice la Y donde la bola intersecta la vertical de la paleta IA.
    Simula rebotes en techo/suelo con plegado.
    Aprende una zona debil (heatmap discreto) para sesgar la prediccion.
    """
    def __init__(self, bins_y: int = 6):
        self.bins_y = int(max(2, bins_y))
        self.bin_h = float(settings.SCREEN_HEIGHT) / float(self.bins_y)
        self.fail_heatmap = np.zeros(self.bins_y, dtype=np.float32)

    def update_on_point_end(self, player_scored: bool, ball_final_y: float):
        # Si anota el jugador, la IA recuerda esa Y como zona debil
        if not player_scored:
            return
        idx = int(_clamp(ball_final_y / self.bin_h, 0, self.bins_y - 1))
        self.fail_heatmap[idx] += 1.0

    def _get_weak_zone_y(self):
        if np.sum(self.fail_heatmap) <= 0.0:
            # Sin datos: empujar a extremos
            return random.choice([settings.BALL_RADIUS * 3.0,
                                  settings.SCREEN_HEIGHT - settings.BALL_RADIUS * 3.0])
        idx = int(np.argmax(self.fail_heatmap))
        return (idx + 0.5) * self.bin_h

    def predict_y(self, ball, ai_paddle, weak_mix: bool = True) -> float:
        vx = float(ball.vx)
        vy = float(ball.vy)
        if abs(vx) < 1e-6:
            return float(ball.y)

        # Tiempo hasta la vertical de la paleta IA
        target_x = float(ai_paddle.x + ai_paddle.width)
        t = (target_x - float(ball.x)) / vx
        if t <= 0.0:
            return float(ball.y)

        y_linear = float(ball.y) + vy * t
        low = float(settings.BALL_RADIUS)
        high = float(settings.SCREEN_HEIGHT - settings.BALL_RADIUS)
        y_fold = _fold_axis(y_linear, low, high)

        if weak_mix:
            weak_y = self._get_weak_zone_y()
            y_fold = 0.75 * y_fold + 0.25 * weak_y

        return _clamp(y_fold, 0.0, float(settings.SCREEN_HEIGHT))