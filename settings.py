# Archivo: settings.py
# Configuracion general del juego (Hand Pong)
# ASCII puro

import cv2

# ---------- Ventana ----------
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
FULLSCREEN = True
WINDOW_NAME = "Hand Pong"
BORDERLESS = True  # la ventana se muestra en modo fullscreen

# ---------- Modo demo / feria ----------
DEMO_MODE = True
if DEMO_MODE:
    SHOW_HAND_SKELETON = False
    HUD_VISIBLE = True
    EDUCATIONAL_MODE = True

# ---------- Pelota ----------
BALL_RADIUS = 16
BALL_COLOR = (255, 255, 255)
BALL_BASE_SPEED = 540.0
BALL_SPEED_X = 540.0
BALL_SPEED_Y = 360.0
BALL_SPEED_INC = 180.0   # px/s^2 aplicado suave
BALL_SPEED_MAX = 1180.0
BALL_SPIN_FACTOR = 260.0
BALL_SPIN_CLAMP = 560.0  # limite de velocidad vertical

# ---------- Paletas ----------
PADDLE_WIDTH = 22
PADDLE_HEIGHT = 184
PADDLE_R_COLOR = (0, 210, 0)      # jugador (derecha)
PADDLE_L_COLOR = (0, 120, 255)    # IA (izquierda)
PLAYER_FOLLOW_ALPHA = 0.36

# ---------- IA humana ----------
AI_DECISION_RATE_HZ = 14.0
AI_LATENCY_MS = 110.0
AI_LATENCY_JITTER_MS = 28.0
AI_SACCADE_AMP_PX = 28.0
AI_MISS_PROB_BASE = 0.08
AI_MISS_PROB_MAX = 0.45
AI_SPEED_FOR_MAX_MISS = 1400.0
AI_D_GAIN = 0.19
AI_DEADBAND_PX = 12.0
AI_MAX_ACCEL = 4300.0
AI_PADDLE_MAX_SPEED = 2100.0

# Curva de "aprendizaje" visual (se mezcla segun tiempo y marcador)
AI_SKILL_START = {
    "miss_base": 0.22,
    "lat_ms": 150.0,
    "decision_hz": 11.0,
    "sacc_amp_px": 34.0,
}
AI_SKILL_END = {
    "miss_base": 0.04,
    "lat_ms": 70.0,
    "decision_hz": 18.0,
    "sacc_amp_px": 20.0,
}
AI_TIME_TO_SKILL = 60.0  # seg para pasar de start a end si el jugador domina

# ---------- Juego ----------
SERVE_COUNTDOWN_SEC = 2.5
ROUND_DURATION_SEC = 45.0
WINNING_SCORE = 5
FPS_CAP = 60

# ---------- Fuente ----------
FONT = cv2.FONT_HERSHEY_SIMPLEX
FONT_SCALE_SCORE = 2.1
FONT_THICKNESS_SCORE = 4

# ---------- Interfaz educativa y HUD ----------
EDUCATIONAL_MODE = True
EDU_PANEL_BG = (12, 18, 26)
EDU_PANEL_ALPHA = 0.72
EDU_TEXT_COLOR = (220, 255, 220)
HUD_BG = (18, 24, 32)
HUD_ALPHA = 0.68
HUD_TEXT_COLOR = (230, 230, 255)
HUD_VALUE_COLOR = (0, 255, 160)
HUD_ALERT_COLOR = (255, 190, 0)
SHOW_HAND_SKELETON = False
TICKER_INTERVAL = 6.0
HUD_VISIBLE = True

# ---------- Visual FX ----------
RING_FADE_TIME = 0.45
FLASH_DECAY_RATE = 0.06
PARTICLE_LIFE = 0.5
PARTICLE_COUNT = 14
PARTICLE_SPEED_MIN = 180.0
PARTICLE_SPEED_MAX = 380.0

# ---------- Hand detector ----------
DETECTION_CONFIDENCE = 0.55
TRACKING_CONFIDENCE = 0.55
HAND_EMA_ALPHA = 0.38
HAND_DEADZONE_PX = 12