# Archivo: opponent_model.py - IA con comportamiento humano
# ASCII puro

import time
import numpy as np
import settings


class OpponentModel:
    """
    Modelo de toma de decision 'humana' para la paleta IA:
    - Tiempo de reaccion (latencia) variable.
    - Prediccion de intercepcion con rebotes verticales.
    - Ruido dependiente del contexto (velocidad, tiempo, marcador).
    - Micro-hesitaciones y saccades (saltos de objetivo).
    - Memoria corta: no cambia de objetivo a >120 Hz.
    """

    def __init__(self):
        seed = int(time.time() * 1000) % (2**32)
        self.rng = np.random.default_rng(seed)
        self.last_target_y = float(settings.SCREEN_HEIGHT / 2.0)
        self.last_clean_pred = self.last_target_y
        self.next_decision_t = 0.0
        self.min_decision_hz = float(getattr(settings, "AI_DECISION_RATE_HZ", 14.0))
        self.hes_active = False
        self.hes_end_t = 0.0

    @staticmethod
    def _reflect_y(y):
        H = float(settings.SCREEN_HEIGHT)
        period = 2.0 * H
        y_mod = y % period
        if y_mod <= H:
            return y_mod
        return period - y_mod

    def _time_to_reach_x(self, ball, x_face):
        vx = float(ball.vx)
        if abs(vx) < 1e-6:
            return None
        if (x_face < ball.x) and (vx < 0.0):
            return max(0.0, (x_face - ball.x) / vx)
        return None

    def _predict_y_at_x(self, ball, x_face, extra_time_s=0.0):
        t = self._time_to_reach_x(ball, x_face)
        if t is None:
            return None, None
        t_total = float(t) + max(0.0, float(extra_time_s))
        y_free = float(ball.y + ball.vy * t_total)
        y_ref = self._reflect_y(y_free)
        y_ref = float(np.clip(y_ref, 0.0, float(settings.SCREEN_HEIGHT)))
        return y_ref, float(t)

    def _miss_probability(self, ball, scores, t_hit):
        base = float(getattr(settings, "AI_MISS_PROB_BASE", 0.05))
        maxp = float(getattr(settings, "AI_MISS_PROB_MAX", 0.45))
        speed = float(np.hypot(ball.vx, ball.vy))
        v_ref = float(getattr(settings, "AI_SPEED_FOR_MAX_MISS", 1400.0))
        p_speed = np.clip(speed / max(1.0, v_ref), 0.0, 1.0)
        if t_hit is None:
            p_time = 0.0
        else:
            p_time = np.clip(1.0 - (t_hit / 1.0), 0.0, 1.0)
        diff = int(scores[0] - scores[1])
        p_score = 0.0 if diff <= 0 else min(0.12, 0.04 * diff)
        p = base + 0.55 * p_speed + 0.50 * p_time + p_score
        return float(np.clip(p, base, maxp))

    def _maybe_hesitate(self, now, t_hit, p_miss):
        if self.hes_active and now < self.hes_end_t:
            return True
        self.hes_active = False
        if t_hit is None:
            return False
        p_hes = np.clip(0.10 + 0.50 * p_miss + 0.30 * np.clip(1.0 - t_hit, 0.0, 1.0), 0.0, 0.65)
        if self.rng.random() < p_hes:
            dur = self.rng.uniform(0.03, 0.10)
            self.hes_active = True
            self.hes_end_t = now + dur
            return True
        return False

    def think(self, ball, ai_paddle, scores, dt):
        now = time.perf_counter()
        if now < self.next_decision_t:
            return self.last_target_y, {"mode": "hold", "y_clean": self.last_clean_pred, "t_hit": None}

        lat_ms = float(getattr(settings, "AI_LATENCY_MS", 90.0))
        lat_jitter = float(getattr(settings, "AI_LATENCY_JITTER_MS", 25.0))
        latency_s = max(0.0, (lat_ms + self.rng.normal(0.0, lat_jitter)) / 1000.0)

        x_face = ai_paddle.x + ai_paddle.width
        y_clean, t_hit = self._predict_y_at_x(ball, x_face, extra_time_s=latency_s)
        if y_clean is None:
            center = float(settings.SCREEN_HEIGHT / 2.0) + float(self.rng.normal(0.0, 20.0))
            center = float(np.clip(center, 0.0, float(settings.SCREEN_HEIGHT)))
            self.last_clean_pred = center
            self.last_target_y = center
            self.next_decision_t = now + (1.0 / self.min_decision_hz)
            return center, {"mode": "center", "y_clean": None, "t_hit": None}

        p_miss = self._miss_probability(ball, scores, t_hit)
        if self._maybe_hesitate(now, t_hit, p_miss):
            self.next_decision_t = now + self.rng.uniform(0.02, 0.05)
            return self.last_target_y, {"mode": "hesitate", "y_clean": y_clean, "t_hit": t_hit}

        sacc_amp = float(getattr(settings, "AI_SACCADE_AMP_PX", 26.0))
        sacc = self.rng.normal(0.0, sacc_amp)
        sigma = 120.0 * p_miss
        noise = float(self.rng.normal(0.0, sigma))
        if t_hit < 0.22:
            noise *= 1.35

        y_target = float(np.clip(y_clean + sacc + noise, 0.0, float(settings.SCREEN_HEIGHT)))
        self.last_clean_pred = float(y_clean)
        self.last_target_y = float(y_target)

        hz = self.min_decision_hz
        if t_hit > 0.8:
            hz *= 0.7
        elif t_hit < 0.25:
            hz *= 1.4
        hz = float(np.clip(hz, 8.0, 24.0))
        self.next_decision_t = now + (1.0 / hz)

        return y_target, {
            "mode": "intercept",
            "y_clean": float(y_clean),
            "t_hit": float(t_hit),
            "p_miss": float(p_miss),
            "noise": float(noise),
            "sacc": float(sacc),
        }

    def get_last_target_y(self):
        return float(self.last_target_y)

    def get_last_clean_prediction_y(self):
        return float(self.last_clean_pred)