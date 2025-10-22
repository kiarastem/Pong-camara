# Archivo: opponent_model.py - IA: prediccion de intercepcion y ruido
# ASCII puro

import numpy as np
import time
import settings


class OpponentModel:
    def __init__(self):
        seed = int(time.time() * 1000) % (2**32)
        self.rng = np.random.default_rng(seed)
        self.last_target_y = float(settings.SCREEN_HEIGHT // 2)

    def predict_intercept_at_x(self, ball, target_x):
        vx = float(ball.vx)
        if vx == 0.0:
            return float(ball.y)
        t = (target_x - ball.x) / vx
        if t < 0.0:
            t = 0.0

        H = float(settings.SCREEN_HEIGHT)
        y = float(ball.y + ball.vy * t)
        period = 2.0 * H
        y_mod = y % period
        if y_mod <= H:
            y_ref = y_mod
        else:
            y_ref = period - y_mod
        y_ref = float(np.clip(y_ref, 0.0, H))
        self.last_target_y = y_ref
        return y_ref

    def apply_error(self, y_target, mistake):
        return float(y_target + self.rng.uniform(-80.0, 80.0) * float(mistake))

    def get_last_target_y(self):
        return float(self.last_target_y)