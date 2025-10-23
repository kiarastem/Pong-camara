# settings.py
# Configuracion general del juego Hand Pong - Version Feria Educativa
# Texto sin tildes (ASCII)

import cv2

# ---------- Ventana ----------
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
FULLSCREEN = True
WINDOW_NAME = "Hand Pong"

# ---------- Estados del juego ----------
MENU      = 0
SERVE     = 1
PLAYING   = 2
PAUSED    = 3
GAME_OVER = 4

# ---------- Pelota ----------
BALL_RADIUS = 14
BALL_COLOR = (255, 255, 255)
INITIAL_BALL_SPEED = 9.0
BALL_MIN_SPEED = 6.0
BALL_MAX_SPEED = 26.0
BALL_SPEED_INC = 0.8
BALL_SPEED_PER_MIN = 3.0
BALL_SPIN_FACTOR = 0.35

# ---------- Paletas ----------
PADDLE_WIDTH = 20
PADDLE_HEIGHT = 160
PADDLE_R_COLOR = (240, 240, 240)
PADDLE_L_COLOR = (240, 240, 240)
AI_PADDLE_MAX_SPEED = 18.0

# ---------- IA adaptativa ----------
AI_DIFFICULTY = "easy"
INITIAL_AI_REACTIVITY = 0.022
AI_REACTIVITY_PER_MIN = 0.018
AI_TIME_EXP = 0.6
AI_MAX_SPEED_START = 0.55
AI_MAX_SPEED_END = 1.10
AI_RAMP_MINUTES = 1.5
AI_ERROR_RATE_START = 0.35
AI_ERROR_RATE_END = 0.10
AI_ERROR_WHIF_TIME = 0.18
AI_AIM_JITTER_PX = 36
AI_LATENCY_MS = 40

# ---------- Juego ----------
SERVE_DELAY = 1.0
WINNING_SCORE = 3
FPS_CAP = 60

# ---------- Tipografia ----------
FONT = cv2.FONT_HERSHEY_SIMPLEX
FONT_SCALE_SCORE = 2.0
FONT_THICKNESS_SCORE = 3
FONT_SCALE_MSG = 1.0
FONT_THICKNESS_MSG = 2
MSG_COLOR = (255, 255, 255)

# ---------- Camara y esqueleto ----------
SHOW_HAND_SKELETON = True
DETECTION_CONFIDENCE = 0.55
TRACKING_CONFIDENCE = 0.55
SKELETON_COLOR = (0, 255, 255)
SKELETON_ALPHA = 0.7
SKELETON_THICKNESS = 2
SKELETON_RADIUS = 5

# ---------- Modo educativo ----------
EDUCATIONAL_MODE = True
EDU_TIPS = [
    "La IA empieza lenta y mejora con el tiempo.",
    "Observa como reacciona mas rapido cuando la pelota se acerca.",
    "El juego termina al llegar a 3 puntos.",
    "Presiona H para mostrar el esqueleto de tu mano."
]

# ---------- Panel de aprendizaje IA ----------
AI_PANEL_ENABLED = True    # se puede alternar con tecla I
AI_PANEL_ALPHA = 0.72
AI_PANEL_BG = (0, 0, 0)
AI_PANEL_TEXT = (235, 235, 235)
AI_PANEL_ACCENT = (0, 255, 160)

# ---------- Camara y esqueleto ----------
SHOW_HAND_SKELETON = True
DETECTION_CONFIDENCE = 0.55
TRACKING_CONFIDENCE = 0.55
SKELETON_COLOR = (0, 255, 255)
SKELETON_ALPHA = 0.7
SKELETON_THICKNESS = 2
SKELETON_RADIUS = 5

# cuantas frames consecutivas para considerar estable la deteccion
SKELETON_STABLE_FRAMES = 3
