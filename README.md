# Hand Pong — Juego educativo con camara e inteligencia artificial

## Descripcion general

**Hand Pong** es una version educativa y moderna del clasico Pong, diseñada para demostrar como la inteligencia artificial puede aprender y adaptarse. El jugador controla su paleta con la **camara y el movimiento de su mano**, mientras la **IA controla la paleta opuesta**, calculando la trayectoria de la pelota y cometiendo errores intencionales para simular aprendizaje humano.

El proyecto busca enseñar los tres pilares basicos de la inteligencia artificial:
1. **Percepcion** — La camara detecta la posicion y el movimiento de la mano.
2. **Decision** — La IA predice la trayectoria de la pelota y decide como moverse.
3. **Adaptacion** — La IA reduce su margen de error con el tiempo, mejorando progresivamente.

Ideal para **ferias educativas, talleres STEM y clases de programacion o IA**.

---

## Caracteristicas principales

- Control por camara en tiempo real usando **MediaPipe**.
- **IA humanizada** con errores iniciales que se reducen conforme avanza la partida.
- **Fisicas naturales** con rebotes realistas y aceleracion progresiva.
- **Efectos visuales** de impacto y animaciones de colision.
- **Interfaz educativa** con panel que muestra:
  - Porcentaje de error de la IA.
  - Prediccion de posicion de la pelota.
  - Velocidad y direccion actual.
- **Menu inicial** y texto de ayuda con los controles.
- **Partidas cortas** (pensadas para ferias o demostraciones publicas).

---

## Controles

| Tecla | Funcion |
|--------|----------|
| ESPACIO | Jugar o pausar |
| R | Reiniciar partida |
| ESC | Salir del juego |
| H | Mostrar / ocultar el esqueleto de la mano |
| G | Activar pantalla completa |
| O | Mostrar panel educativo (IA y datos) |

---

## Instalacion

### 1. Clonar el repositorio
```bash
git clone https://github.com/kiarastem/Pong-camara.git
cd Pong-camara
```

### 2. Crear el entorno virtual (solo la primera vez)
```bash
python -m venv venv
```

### 3. Activar el entorno virtual

#### En Windows (PowerShell o CMD)
```bash
venv\Scripts\activate
```

Si aparece el error:
```
No se puede cargar el archivo ... porque la ejecucion de scripts esta deshabilitada
```
Ejecuta (como administrador):
```bash
Set-ExecutionPolicy Unrestricted -Scope CurrentUser
```
Luego vuelve a activar el entorno.

#### En macOS o Linux
```bash
source venv/bin/activate
```

### 4. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 5. Ejecutar el juego
```bash
python main.py
```

---

## Desactivar el entorno virtual

Cuando termines de trabajar, puedes desactivarlo con:
```bash
deactivate
```

---

## Archivo de inicio rapido (Windows)

Puedes crear un archivo `run.bat` en la carpeta del proyecto con el siguiente contenido:
```bat
@echo off
call venv\Scripts\activate
python main.py
pause
```
De esta manera, basta con hacer doble clic para ejecutar el juego directamente.

---

## Ajustes educativos (archivo settings.py)

- **WINNING_SCORE**: puntos necesarios para ganar (recomendado: 3).
- **BALL_SPEED_INIT**: velocidad inicial de la pelota.
- **BALL_SPEED_INC**: incremento por rebote.
- **AI_ERROR_RATE_START / END**: porcentaje de error de la IA.
- **AI_LEARNING_RATE**: velocidad de aprendizaje de la IA.
- **HAND_EMA_ALPHA**: suavizado de movimiento de la mano.

Ejemplo:
```python
WINNING_SCORE = 3
BALL_SPEED_INIT = 9.0
BALL_SPEED_INC = 0.8
AI_ERROR_RATE_START = 0.25
AI_ERROR_RATE_END = 0.05
AI_LEARNING_RATE = 0.015
```

---

## Buenas practicas para ferias

- Usa **pantalla completa** para mayor impacto visual.
- Configura partidas cortas de **3 a 5 puntos**.
- Explica el **panel educativo** (tecla O) para mostrar como la IA piensa.
- Asegura buena **iluminacion** para deteccion precisa de la mano.
- Prueba la camara antes de cada sesion.

---

## Guion educativo sugerido

1. La camara detecta el movimiento de la mano (percepcion).
2. La IA predice donde estara la pelota (decision).
3. La IA ajusta sus movimientos segun los resultados (adaptacion).
4. Cada rebote acelera la pelota, aumentando la dificultad.
5. El panel educativo muestra el error de la IA y su prediccion en tiempo real.

---

## Estructura del proyecto
```
Pong-camara/
│
├── main.py              # Bucle principal y estados del juego
├── hand_detector.py     # Deteccion de mano y esqueleto
├── game_objects.py      # Fisicas de la pelota y las paletas
├── opponent_model.py    # Modelo de aprendizaje de la IA
├── ai_strategy.py       # Estrategia base de la IA
├── ui_manager.py        # Interfaz y panel educativo
├── settings.py          # Configuracion general
├── requirements.txt     # Dependencias
└── README.md            # Documentacion
```

---

## Solucion de problemas

- **Camara no detectada**: Cierra otras aplicaciones que la usen.
- **Rendimiento bajo**: Reduce la resolucion en `settings.py`.
- **Error con MediaPipe**: Asegura tener Python 3.11 y la version indicada en `requirements.txt`.

---

## Licencia

Proyecto educativo sin fines de lucro. Libre uso en ferias, talleres y actividades academicas, con atribucion a su autora.

**Desarrollado por:**
**Kiara Villarroel P.**  
Ingenieria Civil Informatica — PUCV  
**BETA PUCV — Innovacion y Programacion**