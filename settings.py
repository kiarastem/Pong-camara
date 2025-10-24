# =========================
# VENTANA / VIDEO
# =========================
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FULLSCREEN = False
WINDOW_NAME = "Hand Pong"

# Camara
CAMERA_INDEX = 0
CAMERA_CAPTURE_W = 1280
CAMERA_CAPTURE_H = 720
CAMERA_FPS = 30

# =========================
# ESTADOS
# =========================
SERVE_DELAY = 0.9
WINNING_SCORE = 3  # fin a 3 puntos

# =========================
# PALETAS
# =========================
PADDLE_WIDTH = 18
PADDLE_HEIGHT = 140
PADDLE_L_COLOR = (255, 255, 255)   # IA
PADDLE_R_COLOR = (255, 255, 255)   # Jugador
PADDLE_MAX_SPEED = 1100.0

# =========================
# PELOTA (perfiles de velocidad)
# =========================
BALL_PROFILES = {
    1: {"name": "Lento",  "start": 500.0, "max": 900.0,  "step": 25.0},
    2: {"name": "Normal", "start": 700.0, "max": 1200.0, "step": 40.0},
    3: {"name": "Rapido", "start": 950.0, "max": 1500.0, "step": 60.0},
}
BALL_PROFILE = 2  # por defecto
BALL_MIN_VY = 70.0
BALL_MAX_BOUNCE_DEG = 55.0
BALL_RADIUS = 10
BALL_COLOR = (255, 255, 255)

# =========================
# DETECCION DE MANO
# =========================
DETECTION_CONFIDENCE = 0.7
TRACKING_CONFIDENCE = 0.6
HAND_EMA_ALPHA = 0.28

# =========================
# PANEL EDUCATIVO
# =========================
EDU_PANEL_ENABLED = False   # ahora comienza deshabilitado
EDU_PANEL_ALPHA = 0.35
EDU_PANEL_PADDING = 14
EDU_PANEL_WIDTH_FRAC = 0.28
EDU_TEXT_SCALE = 0.7
EDU_TEXT_THICK = 2
SHOW_PREDICTION = True
PRED_LINE_COLOR = (120, 255, 120)
PRED_LINE_THICK = 2

# =========================
# APRENDIZAJE IA
# =========================
AI_LEARN_BINS = 6
AI_LEARN_RATE = 0.15
AI_HISTORY = 12

# HABILIDAD INICIAL IA (0=tonta, 1=experta)
AI_SKILL_START = 0.35