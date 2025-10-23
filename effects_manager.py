# Archivo: effects_manager.py - Efectos visuales (impactos y flash paletas)
# ASCII puro

import time
import cv2
import numpy as np
import settings


class EffectsManager:
    def __init__(self):
        seed = int(time.time() * 1000) % (2**32)
        self.rng = np.random.default_rng(seed)
        self.particles = []
        self.flashes = []

    def spawn_particles(self, x, y, color=(255, 255, 255)):
        """Spawn particles whose velocities are in px/s (frame-rate independent).

        Particles are updated in draw(...) using the dt passed from the main loop.
        """
        count = int(getattr(settings, "PARTICLE_COUNT", 12))
        life = float(getattr(settings, "PARTICLE_LIFE", 0.45))
        speed_min = float(getattr(settings, "PARTICLE_SPEED_MIN", 160.0))
        speed_max = float(getattr(settings, "PARTICLE_SPEED_MAX", 320.0))
        now = time.time()
        for _ in range(count):
            angle = self.rng.uniform(0.0, 2.0 * np.pi)
            # speed in px/s
            speed = self.rng.uniform(speed_min, speed_max)
            self.particles.append(
                {
                    "x": float(x),
                    "y": float(y),
                    "vx": float(np.cos(angle) * speed),
                    "vy": float(np.sin(angle) * speed),
                    "t": now,
                    "life": life,
                    "color": tuple(int(c) for c in color),
                }
            )

    def flash_paddle(self, x, y, width, height, color=(255, 255, 255)):
        self.flashes.append(
            {
                "x": float(x),
                "y": float(y),
                "w": float(width),
                "h": float(height),
                "t": time.time(),
                "life": 0.18,
                "color": tuple(int(c) for c in color),
            }
        )

    def _draw_particles(self, frame, dt):
        now = time.time()
        survivors = []
        for p in self.particles:
            age = now - p["t"]
            if age > p["life"]:
                continue
            # dt in seconds -> move by vx*dt
            p["x"] += p["vx"] * float(dt)
            p["y"] += p["vy"] * float(dt)
            alpha = max(0.0, 1.0 - age / p["life"])
            color = tuple(int(c * alpha) for c in p["color"])
            cv2.circle(frame, (int(p["x"]), int(p["y"])), 3, color, -1)
            survivors.append(p)
        self.particles = survivors

    def _draw_flashes(self, frame):
        now = time.time()
        survivors = []
        for f in self.flashes:
            age = now - f["t"]
            if age > f["life"]:
                continue
            alpha = max(0.0, 1.0 - age / f["life"])
            overlay = frame.copy()
            color = tuple(int(c * alpha) for c in f["color"])
            cv2.rectangle(
                overlay,
                (int(f["x"]), int(f["y"])),
                (int(f["x"] + f["w"]), int(f["y"] + f["h"])),
                color,
                -1,
            )
            cv2.addWeighted(overlay, 0.4, frame, 0.6, 0, frame)
            survivors.append(f)
        self.flashes = survivors

    def draw(self, frame, dt=1.0 / 60.0):
        """Draw and update effects. Pass dt (seconds) from the main loop for frame-rate independence."""
        self._draw_particles(frame, dt)
        self._draw_flashes(frame)