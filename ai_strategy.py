# ai_strategy.py
# IA hibrida siempre activa (ASCII): simple al inicio, predictiva con mezcla

import random
from typing import Optional
import settings
from opponent_model import OpponentModelAdvanced

def _clamp(v, a, b):
    return max(a, min(b, v))

class _SimpleReactive:
    def __init__(self):
        self.target_y = settings.SCREEN_HEIGHT / 2.0
        self.alpha = 0.22  # suavizado

    def compute(self, ball_y: Optional[float], noise_px: float) -> float:
        if ball_y is None:
            return self.target_y
        self.target_y = (1.0 - self.alpha) * self.target_y + self.alpha * float(ball_y)
        if noise_px > 0.0:
            self.target_y += random.uniform(-noise_px, noise_px) * 0.35
        return _clamp(self.target_y, 0.0, float(settings.SCREEN_HEIGHT))

class OpponentModel:
    """
    Modo feria educativo permanente:
    - Min 0 -> IA simple y torpe (reactiva).
    - Desde switch_min -> mezcla con predictiva (OpponentModelAdvanced).
    - last_target_y expuesto para que main.py lo use.
    """
    def __init__(self):
        self._simple = _SimpleReactive()
        self._advanced = OpponentModelAdvanced()
        self.last_target_y = settings.SCREEN_HEIGHT / 2.0

        self.switch_min = float(getattr(settings, "AI_HYBRID_SWITCH_MIN", 1.0))
        self.ramp_min = float(getattr(settings, "AI_HYBRID_RAMP_MIN", 1.0))
        self.err_start = float(getattr(settings, "AI_ERROR_RATE_START", 0.45))
        self.err_end = float(getattr(settings, "AI_ERROR_RATE_END", 0.15))
        self.jitter_px = float(getattr(settings, "AI_JITTER", 36.0))

    def update(
        self,
        elapsed_min: float,
        ball_y: Optional[float],
        ball_dir: Optional[int],
        paddle_y: Optional[float],
        dt: float,
        *,
        ball=None,
        ai_paddle=None,
        player_paddle=None,
    ) -> float:
        # Mezcla progresiva simple->predictivo
        mix = 1.0 if self.ramp_min <= 0.0 else _clamp((elapsed_min - self.switch_min) / self.ramp_min, 0.0, 1.0)

        # Error humano decreciente
        err_k = _clamp(elapsed_min / max(1e-6, self.switch_min + self.ramp_min), 0.0, 1.0)
        noise_px = (self.err_start + (self.err_end - self.err_start) * err_k) * self.jitter_px

        # Objetivo simple
        y_simple = self._simple.compute(ball_y, noise_px)

        # Objetivo predictivo (si hay objetos completos)
        if ball is not None and ai_paddle is not None:
            y_adv = self._advanced.predict_y(ball, ai_paddle, weak_mix=True)
            y_adv = 0.85 * float(y_adv) + 0.15 * y_simple  # anti vibracion
        else:
            y_adv = y_simple

        # Mezcla final
        self.last_target_y = (1.0 - mix) * y_simple + mix * y_adv
        self.last_target_y = _clamp(self.last_target_y, 0.0, float(settings.SCREEN_HEIGHT))
        return 0.0

    def on_point_end(self, player_scored: bool, ball_final_y: float):
        self._advanced.update_on_point_end(player_scored, ball_final_y)
