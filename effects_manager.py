# Archivo: effects_manager.py - Efectos visuales (impactos y flash paletas)
# ASCII puro

import cv2
import time
import numpy as np


class EffectsManager:
    def __init__(self):
        seed = int(time.time() * 1000) % (2**32)
        self.rng = np.random.default_rng(seed)
        self.particles = []
        self.paddle_flash = []

    def spawn_particles(self, x, y, color=(255, 255, 255), num=12):
        for _ in range(int(num)):
            angle = self.rng.uniform(0.0, 2.0 * np.pi)
            speed = self.rng.uniform(3.0, 8.0)
            vx = np.cos(angle) * speed
            vy = np.sin(angle) * speed
            lifetime = self.rng.uniform(0.2, 0.5)
            self.particles.append(
                {"x": float(x), "y": float(y), "vx": float(vx), "vy": float(vy),
                 "t": time.time(), "life": float(lifetime), "color": tuple(int(c) for c in color)}
            )

    def flash_paddle(self, x, y, width, height, color=(255, 255, 255)):
        self.paddle_flash.append(
            {"x": float(x), "y": float(y), "w": float(width), "h": float(height),
             "t": time.time(), "life": 0.15, "color": tuple(int(c) for c in color)}
        )

    def update_particles(self, frame):
        now = time.time()
        new_particles = []
        for p in self.particles:
            age = now - p["t"]
            if age < p["life"]:
                p["x"] += p["vx"]
                p["y"] += p["vy"]
                alpha = max(0.0, 1.0 - (age / p["life"]))
                col = (int(p["color"][0] * alpha), int(p["color"][1] * alpha), int(p["color"][2] * alpha))
                cv2.circle(frame, (int(p["x"]), int(p["y"])), 3, col, -1)
                new_particles.append(p)
        self.particles = new_particles

    def update_paddle_flash(self, frame):
        now = time.time()
        new_flashes = []
        for f in self.paddle_flash:
            age = now - f["t"]
            if age < f["life"]:
                alpha = max(0.0, 1.0 - (age / f["life"]))
                overlay = frame.copy()
                col = (int(f["color"][0] * alpha), int(f["color"][1] * alpha), int(f["color"][2] * alpha))
                cv2.rectangle(overlay, (int(f["x"]), int(f["y"])),
                              (int(f["x"] + f["w"]), int(f["y"] + f["h"])), col, -1)
                cv2.addWeighted(overlay, 0.4, frame, 0.6, 0, frame)
                new_flashes.append(f)
        self.paddle_flash = new_flashes

    def draw(self, frame):
        self.update_particles(frame)
        self.update_paddle_flash(frame)