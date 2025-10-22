# Hand Pong — Juego educativo con camara y IA (version profesional)

Resumen
-------
Hand Pong es una aplicacion educativa que reinterpreta el clasico juego Pong para visualizar los principios basicos de los sistemas de inteligencia artificial: percepcion, decision y adaptacion. El jugador controla la paleta derecha mediante la camara (MediaPipe Hands) y la paleta izquierda es controlada por una IA que simula comportamiento humano (latencia, ruido, saccades y mejora progresiva).

Objetivos
---------
- Facilitar la comprension practica de conceptos de IA, vision por computador y control.
- Proveer una plataforma segura y ajustable para demostraciones en ferias y talleres STEM.
- Permitir la experimentacion en tiempo real con parametros de percepcion y decision para observacion didactica.

Caracteristicas clave
---------------------
- Control por mano mediante MediaPipe Hands con filtro EMA y fallback cuando MediaPipe no esta disponible.
- Modelo de oponente que simula latencia, jitter, saccades y probabilidad de fallo, con capacidad de mejorar durante la ronda (AISkillManager).
- Control PD para la paleta de la IA con deadband, limites de aceleracion y velocidad maxima variable.
- Fisica de pelota con spin segun punto de impacto, incremento acotado de velocidad y reposicion para evitar dobles colisiones.
- Interfaz educativa: HUD con telemetria, panel inferior con mensajes, countdown de saque y efectos visuales (anillos, flashes, particulas).
- Controles y tuning en vivo (teclas para ajustar parametros durante la demo).

Requisitos
----------
- Python 3.11 recomendado
- Ver `requirements.txt` para versiones concretas de dependencias (numpy, opencv-python, mediapipe==0.10.14, protobuf<5)

Instalacion rapida
------------------
1. Clonar el repositorio:
   git clone https://github.com/kiarastem/Pong-camara.git
2. Crear y activar entorno virtual:
   python -m venv .venv
   - Linux/mac: source .venv/bin/activate
   - Windows: .venv\Scripts\activate
3. Instalar dependencias:
   pip install -r requirements.txt
4. Ejecutar la aplicacion:
   python main.py

Controles principales
---------------------
- ESC : salir
- R   : reiniciar marcador y ronda
- ESPACIO / I : alternar panel educativo
- H   : alternar mini-HUD de telemetria
- K   : alternar dibujo del esqueleto de la mano (MediaPipe)
- P   : pausa / reanudar
- S   : forzar saque
- Q / A : aumentar / disminuir AI_DEADBAND_PX (tuning en vivo)
- W / S : aumentar / disminuir AI_D_GAIN (tuning en vivo)
- E / D : aumentar / disminuir BALL_SPEED_INC (tuning en vivo)
- Z / X : aumentar / disminuir HAND_EMA_ALPHA (tuning en vivo)

Configuracion y afinado (settings.py)
------------------------------------
Los parametros principales se encuentran en `settings.py`. Algunos ejemplos de ajuste rapido para la feria:
- `HAND_EMA_ALPHA`: control de suavizado del seguimiento de la mano (valores mas bajos = movimiento mas suave).
- `HAND_DEADBAND_PX`: zona muerta para evitar movimientos por jitter.
- `AI_DEADBAND_PX`, `AI_D_GAIN`, `AI_MAX_ACCEL`: afectan la estabilidad y reactividad de la paleta IA.
- `BALL_SPEED_INC`, `BALL_SPEED_MAX`: regulan el ritmo e intensidad del juego.

Uso educativo y guion para demostraciones
----------------------------------------
Sugerencia de narrativa breve (1 frase cada 3-5s):
1. "La camara traduce tu mano a una coordenada vertical."
2. "La IA predice donde llegara la pelota considerando rebotes."
3. "La IA tiene latencia y comete errores al inicio, como nosotros."
4. "Con el tiempo y segun el marcador, la IA mejora su precision."
5. "Cada golpe agrega spin y acelera ligeramente la pelota."
6. "Mira la telemetria: latencia, probabilidad de fallo y velocidad."

Estrategias de clase y actividades
---------------------------------
- Analisis de percepcion: observar y explicar el esqueleto de la mano en pantalla.
- Experimento con latencia: cambiar parametros en `settings.py` y comentar resultados.
- Control y retroalimentacion: estudiar el controlador PD de la paleta IA y su respuesta.
- Proyecto de extension: registro anonimo de telemetria para analisis posterior o modo 2 jugadores.

Estructura del proyecto
-----------------------
- `main.py`           : bucle principal, entrada de camara, estado y render.
- `hand_detector.py`  : MediaPipe Hands, EMA y dibujo de esqueleto.
- `game_objects.py`   : Ball, PlayerPaddle, AIPaddle y colisiones.
- `opponent_model.py` : OpponentModel con think(...) y set_skill(...).
- `ui_manager.py`     : HUD, panel educativo, countdown y anillos.
- `effects_manager.py`: particulas y flashes.
- `settings.py`       : parametros y presets para la demo.
- `requirements.txt`  : dependencias.

Contribuir
----------
Aceptamos aportes orientados a mejora de la experiencia educativa:
- Mejora de la estabilidad y compatibilidad con webcams variadas.
- Nuevos modos pedagogicos y perfiles de dificultad.
- Documentacion didactica adicional (docs/education.md).

Problemas comunes y solucion rapida
---------------------------------
- Error al abrir la camara: comprobar que ninguna otra aplicacion la utilice y que `cap.isOpened()` sea True.
- Problemas con MediaPipe o protobuf: usar Python 3.11 y mediapipe==0.10.14 con protobuf<5.
- Bajada de FPS: reducir `BG_BLUR_SCALE` o `PARTICLE_COUNT` en `settings.py`.

Licencia y uso
--------------
Proyecto pensado para uso educativo y demostraciones en ferias. Ajusta `settings.py` para adaptar la dificultad y la narrativa segun la audiencia.

Contacto
--------
Repositorio: https://github.com/kiarastem/Pong-camara
