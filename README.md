# Hand Pong - Juego educativo con camara y IA (ASCII)

Resumen
-------
Hand Pong es una reinterpretacion educativa del clasico Pong que convierte la camara en un sensor de entrada:
el jugador controla la paleta derecha con su mano (MediaPipe Hands) y una IA "humanizada" controla la paleta izquierda.
El proposito es mostrar en vivo los tres componentes basicos de un sistema inteligente:
- Percepcion (la camara y el esqueleto de la mano)
- Decision (la IA predice donde la pelota impactara)
- Adaptacion / aprendizaje simulado (la IA mejora su habilidad segun tiempo y marcador)

Caracteristicas principales
---------------------------
- Control por mano usando MediaPipe con fallback seguro si MediaPipe no esta disponible.
- IA que simula latencia, jitter, saccades y probabilidad de fallo, y que mejora progresivamente.
- Fisica de pelota con spin dependiente del punto de impacto y incremento acotado de velocidad.
- Control PD para paleta IA con deadband, limite de aceleracion y velocidad maxima dinamica.
- HUD educativo con telemetria (velocidad de pelota, latencia IA, probabilidad de fallo, decision_hz).
- Efectos visuales: anillos de impacto, flashes y particulas.
- Modo fullscreen 1920x1080 por defecto (configurable).

Instalacion rapida
------------------
1. Recomendado: Python 3.11
2. Crear y activar entorno virtual:
   - linux/mac: python -m venv .venv && source .venv/bin/activate
   - windows: python -m venv .venv && .venv\\Scripts\\activate
3. Instalar dependencias:
   - pip install -r requirements.txt
4. Ejecutar demo:
   - python main.py

Requisitos
----------
Ver `requirements.txt` para versiones especificas. Principales dependencias:
- numpy
- opencv-python
- mediapipe==0.10.14
- protobuf<5

Controles (teclado)
-------------------
- ESC : salir
- R   : reiniciar marcador y ronda
- ESPACIO / I : toggle panel educativo inferior
- H   : toggle HUD de telemetria
- K   : toggle dibujo del esqueleto de la mano (mostrar percepcion en vivo)
- P   : pausa / reanudar
- S   : forzar saque
- Q / A : aumentar / disminuir AI_DEADBAND_PX (tuning en vivo)
- W / S : aumentar / disminuir AI_D_GAIN (tuning en vivo)
- E / D : aumentar / disminuir BALL_SPEED_INC (tuning en vivo)
- Z / X : aumentar / disminuir HAND_EMA_ALPHA (tuning en vivo)

Concepto pedagogico
-------------------
Hand Pong fue diseñado para ferias y talleres STEM. Con este proyecto los alumnos pueden:
- Ver como la camara traduce una mano a coordenadas y como ese dato se suaviza.
- Observar la prediccion de la IA (linea de prediccion y telemetria).
- Experimentar con latencia y error modificando parametros.
- Comprender control PD y la gestion de errores humanos simulados.

Archivo de configuracion (settings.py)
-------------------------------------
Ajusta la experiencia sin tocar la logica:
- HAND_EMA_ALPHA, HAND_DEADZONE_PX: suavizado y tolerancia del seguimiento de la mano.
- AI_DEADBAND_PX, AI_D_GAIN, AI_MAX_ACCEL: estabilidad y respuesta de la paleta IA.
- BALL_SPEED_INC, BALL_SPEED_MAX, BALL_RADIUS: ritmo de juego y visibilidad.
Consulta `settings.py` para comentarios y rangos recomendados.

Tuning rapido (para la feria)
-----------------------------
- Hacer la IA mas facil: aumentar AI_DEADBAND_PX, reducir AI_D_GAIN y bajar BALL_SPEED_INC.
- Hacer la IA mas desafiante: disminuir AI_DEADBAND_PX, aumentar AI_D_GAIN y subir BALL_SPEED_INC.
- Reducir jitter de la mano: bajar HAND_EMA_ALPHA (hace mas suave) o aumentar HAND_DEADZONE_PX.

Modo offline / fallback
-----------------------
Si MediaPipe no esta instalado o falla, el juego continua:
- La paleta del jugador se mantiene estable (fallback suave hacia el centro).
- La IA y la fisica siguen funcionando para demostraciones sin sensor.

Estructura del codigo
---------------------
- main.py           : bucle principal, entrada, estado, render y controles.
- hand_detector.py  : integracion con MediaPipe y filtro EMA para Y de la palma.
- game_objects.py   : Ball, PlayerPaddle, AIPaddle y logica de colisiones.
- opponent_model.py : OpponentModel.think(...) devuelve objetivo y telemetria.
- ui_manager.py     : HUD, panel educativo, countdown y anillos.
- effects_manager.py: particulas y flashes visuales.
- settings.py       : parametros y presets para la feria.
- requirements.txt  : dependencias.

Sugerencias para docentes
-------------------------
- Antes de la demo, calibrar HAND_EMA_ALPHA y HAND_DEADZONE_PX con la camara usada.
- Practicar rondas cortas: ROUND_DURATION_SEC = 45s y WINNING_SCORE = 5 funcionan bien para rotacion de publico.
- En clase, pedir a estudiantes que cambien parametros y observen efectos en telemetria.

Problemas comunes y soluciones
-----------------------------
- No detecta la camara: comprobar `cap.isOpened()` y que ninguna otra app use la camara.
- Errores de MediaPipe / protobuf: usar Python 3.11 con mediapipe==0.10.14 y protobuf<5.
- FPS bajos: reducir BG_BLUR_SCALE en settings.py y disminuir PARTICLE_COUNT.

Proxima tarea sugerida
----------------------
- Ejecutar pruebas unitarias headless para OpponentModel y PD controller.
- Añadir un documento `docs/education.md` con el guion pedagogico y actividades de aula.
- Preparar un branch para perfiles de dificultad predefinidos (kid/normal/pro).

Licencia y uso
--------------
Proyecto pensado para propósitos educativos y demostraciones en ferias.
Ajusta `settings.py` para adaptar la dificultad y narrativa pedagogica.

----------------
Repositorio: https://github.com/kiarastem/Pong-camara