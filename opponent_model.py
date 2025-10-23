# opponent_model.py
"""
OpponentModel: tracks AI behavior and internal state for educational display.

Purpose:
---------
Provides introspection into how the AI evolves — tracking its
error rate, prediction accuracy, and latency adjustments over time.

The goal is to make the AI’s “thought process” visible to the player
through the educational HUD (bottom panel).
"""

import numpy as np
import time
import settings


class OpponentModel:
    def __init__(self):
        self.last_prediction_y = settings.SCREEN_HEIGHT / 2
        self.last_error = 0.0
        self.last_latency = settings.AI_LATENCY_MS
        self.decision_rate = 1.0 / max(1e-6, getattr(settings, "AI_DECISION_RATE_HZ", 15))
        self.timer = 0.0
        self.learn_start = time.time()

    def update(self, ball, paddle):
        """
        Simulates AI perception & prediction every few frames.
        Returns predicted y-coordinate and diagnostic info.
        """
        now = time.time()
        dt = now - self.timer
        if dt < self.decision_rate:
            return self.last_prediction_y, {}

        self.timer = now
        info = {}

        # Predict where the ball will intersect the paddle
        if abs(ball.vel_x) > 0.01:
            t_to_paddle = (paddle.x - ball.x) / ball.vel_x
            y_pred = ball.y + ball.vel_y * t_to_paddle
        else:
            y_pred = ball.y

        # Add bounded reflection (like bouncing prediction)
        y_pred = np.clip(y_pred, 0, settings.SCREEN_HEIGHT)
        elapsed = (now - self.learn_start) / 60.0

        # AI becomes more accurate with time
        progress = min(1.0, elapsed / getattr(settings, "AI_RAMP_MINUTES", 3.0))
        error_factor = np.interp(progress,
                                 [0, 1],
                                 [settings.AI_ERROR_RATE_START, settings.AI_ERROR_RATE_END])
        noise = np.random.uniform(-60, 60) * error_factor
        y_pred += noise

        # Latency improves slowly (reaction time)
        self.last_latency = settings.AI_LATENCY_MS * (1.0 - 0.5 * progress)
        latency_delay = self.last_latency / 1000.0
        self.last_prediction_y = (1 - latency_delay) * self.last_prediction_y + latency_delay * y_pred

        # Track last deviation (for HUD visualization)
        self.last_error = abs(noise)
        info.update({
            "prediction_y": self.last_prediction_y,
            "error_px": self.last_error,
            "latency_ms": self.last_latency,
            "progress": progress
        })
        return self.last_prediction_y, info

    def get_debug_text(self):
        """Returns a short text summary for the HUD educational panel."""
        return (
            f"AI latency {self.last_latency:.0f}ms | "
            f"error ±{self.last_error:.0f}px"
        )