# Archivo: opponent_model.py
# IA con latencia, ruido, saccades y probabilidad de fallo (estilo humano)
# ASCII puro

import time
import numpy as np
import settings


class OpponentModel:
    def __init__(self):
        seed = int(time.time() * 1000) % (2**32)
        self.rng = np.random.default_rng(seed)
        self.skill = dict(settings.AI_SKILL_START)
        self.last_target_y = float(settings.SCREEN_HEIGHT / 2.0)
        self.last_clean_pred = self.last_target_y
        self.next_decision_t = 0.0
        self.last_info = {"mode": "init", "y_clean": self.last_clean_pred, "t_hit": None,
                          "p_miss": self.skill["miss_base"], "lat_ms": self.skill["lat_ms"]}

    def set_skill(self, **overrides):
        for k, v in overrides.items():
            if k in self.skill:
                self.skill[k] = float(v)

    @staticmethod
    def _reflect_y(y):
        h = float(settings.SCREEN_HEIGHT)
        period = 2.0 * h
        y_mod = y % period
        if y_mod <= h:
            return y_mod
        return period - y_mod

    def _time_to_reach_x(self, ball, x_face):
        vx = float(ball.vx)
        if abs(vx) < 1e-5 or x_face >= ball.x:
            return None
        return max(0.0, (x_face - ball.x) / vx)

    def _predict_y_at_x(self, ball, x_face, latency_s):
        t_hit = self._time_to_reach_x(ball, x_face)
        if t_hit is None:
            return None, None
        t_total = t_hit + max(0.0, latency_s)
        y_future = ball.y + ball.vy * t_total
        y_ref = self._reflect_y(y_future)
        return float(np.clip(y_ref, 0.0, settings.SCREEN_HEIGHT)), float(t_hit)

    def _miss_probability(self, ball, scores, t_hit):
        base = float(self.skill.get("miss_base", settings.AI_MISS_PROB_BASE))
        maxp = float(settings.AI_MISS_PROB_MAX)
        speed = float(np.hypot(ball.vx, ball.vy))
        v_ref = float(settings.AI_SPEED_FOR_MAX_MISS)
        p_speed = np.clip(speed / max(1.0, v_ref), 0.0, 1.0)
        if t_hit is None:
            p_time = 0.0
        else:
            p_time = np.clip(1.0 - (t_hit / 0.9), 0.0, 1.0)
        diff = int(scores[0] - scores[1])  # IA - Jugador
        p_score = 0.02 * max(0, diff)
        p = base + 0.55 * p_speed + 0.40 * p_time + p_score
        return float(np.clip(p, base, maxp))

    def _maybe_hesitate(self, now, t_hit, p_miss):
        if t_hit is None:
            return False
        base = 0.12
        boost = 0.4 * np.clip(1.0 - t_hit, 0.0, 1.0)
        miss_factor = 0.6 * p_miss
        p_hes = np.clip(base + boost + miss_factor, 0.0, 0.68)
        return self.rng.random() < p_hes

    def think(self, ball, ai_paddle, scores, dt):
        now = time.perf_counter()
        if now < self.next_decision_t:
            return self.last_target_y, self.last_info

        lat_ms = float(self.skill.get("lat_ms", settings.AI_LATENCY_MS))
        lat_jit = float(settings.AI_LATENCY_JITTER_MS)
        latency_s = max(0.0, (lat_ms + self.rng.normal(0.0, lat_jit)) / 1000.0)

        x_face = ai_paddle.x + ai_paddle.width
        y_clean, t_hit = self._predict_y_at_x(ball, x_face, latency_s)

        if y_clean is None:
            center = float(settings.SCREEN_HEIGHT / 2.0)
            noise = self.rng.normal(0.0, 45.0)
            target = float(np.clip(center + noise, 0.0, settings.SCREEN_HEIGHT))
            self.last_target_y = target
            self.last_clean_pred = target
            hz = float(self.skill.get("decision_hz", settings.AI_DECISION_RATE_HZ))
            self.next_decision_t = now + (1.0 / hz)
            self.last_info = {"mode": "center", "y_clean": None, "t_hit": None,
                              "p_miss": self.skill["miss_base"], "lat_ms": lat_ms}
            return target, self.last_info

        p_miss = self._miss_probability(ball, scores, t_hit)

        if self._maybe_hesitate(now, t_hit, p_miss):
            delay = self.rng.uniform(0.03, 0.08)
            self.next_decision_t = now + delay
            self.last_info = {"mode": "hesitate", "y_clean": float(y_clean), "t_hit": float(t_hit),
                              "p_miss": float(p_miss), "lat_ms": float(lat_ms)}
            return self.last_target_y, self.last_info

        sacc_amp = float(self.skill.get("sacc_amp_px", settings.AI_SACCADE_AMP_PX))
        sacc = self.rng.normal(0.0, sacc_amp)
        noise_sigma = 140.0 * p_miss
        if t_hit is not None and t_hit < 0.25:
            noise_sigma *= 1.3
        noise = self.rng.normal(0.0, noise_sigma)

        target = float(np.clip(y_clean + sacc + noise, 0.0, settings.SCREEN_HEIGHT))
        self.last_clean_pred = float(y_clean)
        self.last_target_y = target

        hz = float(self.skill.get("decision_hz", settings.AI_DECISION_RATE_HZ))
        if t_hit is not None:
            if t_hit > 0.9:
                hz *= 0.75
            elif t_hit < 0.25:
                hz *= 1.45
        hz = float(np.clip(hz, 8.0, 24.0))
        jitter = self.rng.uniform(-0.6, 0.4)
        self.next_decision_t = now + max(0.02, (1.0 / hz) + jitter * 0.01)

        self.last_info = {
            "mode": "intercept",
            "y_clean": float(y_clean),
            "t_hit": float(t_hit) if t_hit is not None else None,
            "p_miss": float(p_miss),
            "lat_ms": float(lat_ms),
            "noise": float(noise),
            "sacc": float(sacc),
        }
        return target, self.last_info

    def get_last_clean_prediction_y(self):
        return float(self.last_clean_pred)