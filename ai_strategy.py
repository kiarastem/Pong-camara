# ai_strategy.py
# IA educativa simplificada y progresiva

import random
from typing import Optional

import settings
from opponent_model import OpponentModelAdvanced


def _clamp(v, a, b):
    return max(a, min(b, v))


class _SimpleReactive:
    def __init__(self):
        self.target_y = settings.SCREEN_HEIGHT / 2.0
        self.alpha = 0.22

    def compute(self, ball_y: Optional[float], noise_px: float) -> float:
        if ball_y is None:
            return self.target_y
        self.target_y = (1.0 - self.alpha) * self.target_y + self.alpha * float(ball_y)
        if noise_px > 0.0:
            self.target_y += random.uniform(-noise_px, noise_px) * 0.35
        return _clamp(self.target_y, 0.0, float(settings.SCREEN_HEIGHT))


class OpponentModel:
    def __init__(self):
        self._simple = _SimpleReactive()
        self._advanced = OpponentModelAdvanced()
        self.last_target_y = settings.SCREEN_HEIGHT / 2.0
        self.err_rate = 1.0
        self.mix = 0.0
        self.adv_pred_y = None

        self.switch_min = 1.0
        self.ramp_min = 1.0
        self.err_start = 0.45
        self.err_end = 0.15
        self.jitter_px = 36.0

    def update(self, elapsed_min, ball_y, ball_dir, paddle_y, dt, *, ball=None, ai_paddle=None, player_paddle=None):
        self.mix = _clamp((elapsed_min - self.switch_min) / self.ramp_min, 0.0, 1.0)
        err_k = _clamp(elapsed_min / max(1e-6, self.switch_min + self.ramp_min), 0.0, 1.0)
        self.err_rate = _clamp(self.err_start + (self.err_end - self.err_start) * err_k, 0.0, 1.0)
        noise_px = self.err_rate * self.jitter_px

        y_simple = self._simple.compute(ball_y, noise_px)

        self.adv_pred_y = None
        if ball is not None and ai_paddle is not None:
            y_adv = self._advanced.predict_y(ball, ai_paddle, weak_mix=True)
            self.adv_pred_y = float(y_adv)
            y_adv = 0.85 * float(y_adv) + 0.15 * y_simple
        else:
            y_adv = y_simple

        self.last_target_y = (1.0 - self.mix) * y_simple + self.mix * y_adv
        self.last_target_y = _clamp(self.last_target_y, 0.0, float(settings.SCREEN_HEIGHT))
        return 0.0