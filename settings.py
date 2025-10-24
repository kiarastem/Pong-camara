# settings.py
# Configuración central - Modo feria (educativo, rápido y visualmente claro)

# --- Estados del juego ---
MENU = "MENU"
SERVE = "SERVE"
PLAYING = "PLAYING"
PAUSED = "PAUSED"
GAME_OVER = "GAME_OVER"

# --- Tamaño base y ventana ---
BASE_WIDTH = 1280
BASE_HEIGHT = 720
SCREEN_WIDTH = BASE_WIDTH
SCREEN_HEIGHT = BASE_HEIGHT
AUTO_FULLSCREEN = True

# --- Cámara (ajustada para carga más rápida) ---
CAMERA_CAPTURE_W = 640
CAMERA_CAPTURE_H = 360
CAMERA_FPS = 30
CAMERA_FILL = True  # fondo visible en tiempo real

# --- Estilo Pong clásico ---
BALL_RADIUS = 12
BALL_COLOR = (255, 255, 255)
PADDLE_WIDTH = 20
PADDLE_HEIGHT = 120
PADDLE_L_COLOR = (255, 255, 255)
PADDLE_R_COLOR = (255, 255, 255)

# --- Velocidad más alta desde el inicio ---
BALL_BASE_SPEED = 900.0
BALL_MAX_SPEED = 1600.0
BALL_ACCEL = 1.1
BALL_SPEED_LIMIT = 0.96

# --- Partidas cortas (ideal feria) ---
WINNING_SCORE = 3
SERVE_DELAY = 0.5

# --- Inteligencia artificial ajustada ---
AI_HYBRID_SWITCH_MIN = 1.5
AI_HYBRID_RAMP_MIN = 1.0
AI_ERROR_RATE_START = 0.35
AI_ERROR_RATE_END = 0.05
AI_JITTER = 30

# --- Control por mano ---
DETECTION_CONFIDENCE = 0.6
SKELETON_ALPHA = 0.6
SKELETON_STABLE_FRAMES = 3
HAND_LERP_ALPHA = 0.25

# --- Interfaz visual ---
import cv2
FONT = cv2.FONT_HERSHEY_SIMPLEX
FONT_SCALE_SCORE = 3.0
FONT_THICKNESS_SCORE = 5
FONT_SCALE_MSG = 1.0
FONT_THICKNESS_MSG = 2
MSG_COLOR = (255, 255, 255)
SCORE_COLOR_AI = (240, 70, 70)
SCORE_COLOR_PLAYER = (70, 240, 70)
WINDOW_NAME = "Hand Pong - Modo Feria"

# --- Mensajes educativos ---
EDU_TIPS = [
    "La IA mejora observando el movimiento de la pelota.",
    "Cada golpe acelera la pelota un poco más.",
    "Usa tu mano para controlar la paleta derecha.",
]

# --- Escalado dinámico ---
_BASES = {
    "PADDLE_WIDTH": PADDLE_WIDTH,
    "PADDLE_HEIGHT": PADDLE_HEIGHT,
    "BALL_RADIUS": BALL_RADIUS,
    "BALL_BASE_SPEED": BALL_BASE_SPEED,
}
def apply_resolution(width, height):
    global SCREEN_WIDTH, SCREEN_HEIGHT
    SCREEN_WIDTH, SCREEN_HEIGHT = int(width), int(height)
    s = SCREEN_HEIGHT / float(BASE_HEIGHT)
    for k in ("PADDLE_WIDTH", "PADDLE_HEIGHT", "BALL_RADIUS"):
        globals()[k] = max(6, int(_BASES[k] * s))
    globals()["BALL_BASE_SPEED"] = float(_BASES["BALL_BASE_SPEED"] * s)