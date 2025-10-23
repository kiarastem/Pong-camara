# Hand Pong — Juego educativo con cámara y IA (versión profesional)

Resumen ejecutivo
-----------------
Hand Pong transforma el clásico Pong en una herramienta pedagógica para visualizar, en tiempo real, los tres bloques esenciales de un sistema inteligente: percepción (la cámara y el esqueleto de la mano), decisión (predicción de trayectoria) y adaptación (mejora simulada de la IA). Está pensado para ferias, talleres STEM y clases donde se exploran visión por computador, control y conceptos básicos de IA.

Estado del proyecto
-------------------
- Lenguaje: Python 3.11 (recomendado)
- Resolución objetivo: 1920×1080 (fullscreen configurable)
- Dependencias clave: numpy, opencv-python, mediapipe==0.10.14, protobuf<5
- Rama de trabajo con estas mejoras: `improve/hand-skeleton`

Características principales
--------------------------
- Control por mano (paleta derecha) mediante MediaPipe Hands con filtrado EMA, deadzone y fallback seguro.
- Oponente controlado por un modelo que simula comportamiento humano (latencia, jitter, saccades, probabilidad de fallo) y que mejora progresivamente durante la ronda (AISkillManager).
- Control PD en la paleta IA con deadband, límite de aceleración y velocidad máxima dinámica para evitar vibraciones.
- Física de la pelota con spin dependiente del punto de impacto, incremento acotado de velocidad y corrección de solapamiento para evitar colisiones dobles.
- HUD educativo: telemetría en pantalla (velocidad de la pelota, latencia IA, p_miss, decision_hz), panel inferior con explicaciones, ticker de tips y overlay de parámetros tunables en vivo.
- Efectos visuales (anillos de impacto, flashes de paleta, partículas) con integración dependiente de dt.
- Control en tiempo real y herramientas de tuning (teclas para ajustar parámetros durante la demo).
- Visualización del esqueleto de la mano (toggle) para explicar percepción.

Instalación (rápida)
--------------------
1. Clonar el repositorio:
   git clone https://github.com/kiarastem/Pong-camara.git
2. Crear y activar entorno virtual:
   python -m venv .venv
   - Linux/mac: source .venv/bin/activate
   - Windows: .venv\Scripts\activate
3. Instalar dependencias:
   pip install -r requirements.txt
4. Ejecutar:
   python main.py

Controles y tuning en vivo
--------------------------
- ESC : salir
- R   : reiniciar marcador y ronda
- ESPACIO / I : alternar panel educativo (inferior)
- H   : alternar mini-HUD de telemetría
- K   : alternar dibujo del esqueleto de la mano (MediaPipe)
- P   : pausa / reanudar
- S   : forzar saque
- Q / A : aumentar / disminuir AI_DEADBAND_PX (ajuste fino)
- W / S : aumentar / disminuir AI_D_GAIN (derivativo)
- E / D : aumentar / disminuir BALL_SPEED_INC (incremento de velocidad por golpe)
- Z / X : aumentar / disminuir HAND_EMA_ALPHA (suavizado del seguimiento de la mano)

Archivo de configuración (settings.py)
--------------------------------------
Todas las constantes de comportamiento están en `settings.py`. Los parámetros más relevantes para demos y talleres:

- Percepción:
  - HAND_EMA_ALPHA: coeficiente EMA (0..1). Valores más bajos = movimiento más suave.
  - HAND_DEADBAND_PX: zona muerta en pixeles.
  - SHOW_HAND_SKELETON: mostrar esqueleto por defecto.

- IA:
  - AI_DEADBAND_PX: zona muerta para la paleta IA.
  - AI_D_GAIN / AI_P_GAIN: ganancias PD.
  - AI_MAX_ACCEL: límite de aceleración de la paleta IA.
  - AI_DECISION_RATE_HZ / AI_LATENCY_MS / AI_MISS_PROB_BASE: control de comportamiento humano.

- Pelota:
  - BALL_SPEED_INC: incremento por golpe (aditivo).
  - BALL_SPEED_MAX: velocidad máxima.
  - BALL_SPIN_FACTOR / BALL_SPIN_CLAMP: control de spin.

Buenas prácticas para la feria
-----------------------------
- Calibrar HAND_EMA_ALPHA y HAND_DEADBAND_PX según la cámara y la iluminación del puesto.
- Mantener ROUND_DURATION_SEC y WINNING_SCORE en valores cortos (ej. 45 s / 5 puntos) para rotación de público.
- Cerrar aplicaciones que usen la cámara para evitar conflictos.
- Probar el modo fallback (sin MediaPipe) antes del evento en caso de problemas de instalación.

Guion pedagógico y usos en clase
-------------------------------
Breve guion para presentaciones (frases de ~3-5s):
1. "La cámara traduce tu mano a una coordenada vertical."
2. "La IA predice dónde llegará la pelota considerando rebotes."
3. "La IA simula latencia y comete errores al inicio, como nosotros."
4. "Con tiempo y presión, la IA adapta su habilidad."
5. "Cada impacto genera spin y acelera la pelota ligeramente."
6. "Observa la telemetría: latencia, p_miss y velocidad."

Actividades didácticas sugeridas
- Observación guiada del esqueleto de la mano: discutir cómo la percepción se traduce en acción.
- Experimentos controlados: cambiar latencia o probabilidad de fallo y comparar resultados.
- Análisis del controlador PD: visualizar overshoot y ajustar ganancias.
- Extensiones: modo 2 jugadores, registro anónimo de telemetría para análisis académico.

Estructura del repositorio
--------------------------
- main.py           — bucle principal, estados y render.
- hand_detector.py  — MediaPipe + EMA + dibujo de esqueleto.
- game_objects.py   — Ball, PlayerPaddle, AIPaddle y colisiones.
- opponent_model.py — OpponentModel con think(...) y set_skill(...).
- ui_manager.py     — HUD, panel educativo, countdown y rings.
- effects_manager.py— partículas, flashes y efectos.
- settings.py       — parámetros y presets.
- requirements.txt  — dependencias.

Desarrollo y contribuciones
---------------------------
- Abrir issues para reportar bugs o solicitar features (modos pedagógicos, perfiles de dificultad).
- Pull requests con tests ligeros (simulaciones headless) serán bienvenidos.
- Se sugiere incluir ejemplos de configuración y guiones didácticos en `docs/education.md`.

Problemas frecuentes y soluciones rápidas
----------------------------------------
- La cámara no se abre: comprobar que `cap.isOpened()` y que la cámara no esté siendo usada por otra app.
- Errores de MediaPipe/protobuf: usar Python 3.11 con mediapipe==0.10.14 y protobuf<5.
- FPS bajos: reducir `BG_BLUR_SCALE` y `PARTICLE_COUNT` en `settings.py`.

Licencia y uso
--------------
Proyecto orientado a la educación y demostraciones públicas. Ajustar `settings.py` y los textos pedagógicos para el público objetivo. Consultar al responsable del puesto para la política de uso en eventos.

Contacto
--------
Repositorio: https://github.com/kiarastem/Pong-camara