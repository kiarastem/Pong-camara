# effects_manager.py
"""
Educational visual effects manager for Hand Pong.
Adds lightweight particle bursts, paddle flashes and impact rings
to reinforce learning feedback (hit / miss visualization).

Aligned with the minimal, clean design philosophy:
- Simple geometry (rings, rectangles, fading dots)
- No color clutter; uses soft whites and educational highlights
"""

import cv2
import numpy as np
import time
import settings


class EffectsManager:
    def __init__(self):
        self.particles = []
        self.flashes = []
        self.rings = []

    # ------------------- PARTICLE BURST -------------------
    def spawn_particles(self, x, y, color=(255, 255, 255), count=10):
        """Creates a short burst of particles from (x, y)."""
        for _ in range(count):
            angle = np.random.uniform(0, 2 * np.pi)
            speed = np.random.uniform(3.0, 8.0)
            vx, vy = np.cos(angle) * speed, np.sin(angle) * speed
            self.particles.append({
                "x": x, "y": y,
                "vx": vx, "vy": vy,
                "life": np.random.uniform(0.3, 0.6),
                "t": time.time(),
                "color": color
            })

    # ------------------- PADDLE FLASH -------------------
    def flash_paddle(self, x, y, w, h, color=(100, 180, 255)):
        """Highlights the paddle area briefly when it hits."""
        self.flashes.append({
            "x": x, "y": y, "w": w, "h": h,
            "color": color, "t": time.time()
        })

    # ------------------- RING EFFECT -------------------
    def spawn_ring(self, x, y, color=(255, 255, 255)):
        """Expanding circle when the ball hits a paddle."""
        self.rings.append({"x": x, "y": y, "t": time.time(), "color": color})

    # ------------------- DRAW EVERYTHING -------------------
    def draw(self, frame, dt=0.016):
        now = time.time()
        self._draw_particles(frame, now, dt)
        self._draw_flashes(frame, now)
        self._draw_rings(frame, now)

    # ------------------- HELPERS -------------------
    def _draw_particles(self, frame, now, dt):
        alive = []
        for p in self.particles:
            age = now - p["t"]
            if age > p["life"]:
                continue
            fade = 1.0 - (age / p["life"])
            p["x"] += p["vx"] * dt * 60.0
            p["y"] += p["vy"] * dt * 60.0
            color = tuple(int(c * fade) for c in p["color"])
            cv2.circle(frame, (int(p["x"]), int(p["y"])), 2, color, -1, cv2.LINE_AA)
            alive.append(p)
        self.particles = alive

    def _draw_flashes(self, frame, now):
        """Draws quick flash rectangles around paddle hits."""
        overlay = frame.copy()
        remaining = []
        for f in self.flashes:
            age = now - f["t"]
            if age < 0.12:
                alpha = 1.0 - (age / 0.12)
                color = tuple(int(c * alpha) for c in f["color"])
                cv2.rectangle(overlay, (int(f["x"]), int(f["y"])),
                              (int(f["x"] + f["w"]), int(f["y"] + f["h"])),
                              color, 2)
                remaining.append(f)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
        self.flashes = remaining

    def _draw_rings(self, frame, now):
        """Draws soft expanding rings on ball–paddle contact."""
        alive = []
        for r in self.rings:
            age = now - r["t"]
            if age > 0.5:
                continue
            alpha = 1.0 - (age / 0.5)
            radius = int(10 + 150 * age)
            color = tuple(int(c * alpha) for c in r["color"])
            cv2.circle(frame, (int(r["x"]), int(r["y"])), radius, color, 1, cv2.LINE_AA)
            alive.append(r)
        self.rings = alive