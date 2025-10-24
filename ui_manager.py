# ui_manager.py
# Interfaz del juego y panel educativo (todo en español y ASCII)

import cv2
import settings


class UIManager:
    def draw_center_line(self, frame, dash=26, gap=22, thick=3):
        """Linea punteada central tipo Pong."""
        xmid = settings.SCREEN_WIDTH // 2
        for y in range(0, settings.SCREEN_HEIGHT, dash + gap):
            cv2.line(frame, (xmid, y), (xmid, y + dash), (255, 255, 255), thick)

    def draw_scores(self, frame, score_ia, score_jugador):
        """Marcadores grandes y contrastados en los bordes superiores."""
        cv2.putText(
            frame, str(score_ia),
            (settings.SCREEN_WIDTH // 4, 110),
            settings.FONT, 2.4, (255, 100, 100), 4, cv2.LINE_AA
        )
        cv2.putText(
            frame, str(score_jugador),
            (settings.SCREEN_WIDTH * 3 // 4 - 60, 110),
            settings.FONT, 2.4, (100, 255, 100), 4, cv2.LINE_AA
        )

    def draw_menu(self, frame, subtitulo=""):
        """Pantalla de inicio simple en ASCII."""
        self._texto_centrado(frame, "HAND PONG", settings.SCREEN_HEIGHT // 2 - 110, True)
        if subtitulo:
            self._texto_centrado(frame, subtitulo, settings.SCREEN_HEIGHT // 2 - 52, False)
        self._texto_centrado(frame, "Presiona ESPACIO para comenzar", settings.SCREEN_HEIGHT // 2 + 60, False)

    def draw_footer_help(self, frame):
        """Controles en la parte inferior, mas grandes y legibles."""
        texto = (
            "ESPACIO: jugar/pausar  |  R: reiniciar  |  ESC: salir  |  "
            "H: esqueleto  |  G: pantalla completa  |  O: panel educativo"
        )
        escala = 0.95
        (tw, _), _ = cv2.getTextSize(texto, settings.FONT, escala, 2)
        x = max(10, (settings.SCREEN_WIDTH - tw) // 2)
        y = settings.SCREEN_HEIGHT - 18
        cv2.putText(frame, texto, (x, y), settings.FONT, escala, (220, 220, 220), 2, cv2.LINE_AA)

    def draw_center_message(self, frame, mensaje, sub_mensaje=""):
        """Mensajes centrados (pausa, fin, aviso de saque)."""
        self._texto_centrado(frame, mensaje, settings.SCREEN_HEIGHT // 2 - 40, True)
        if sub_mensaje:
            self._texto_centrado(frame, sub_mensaje, settings.SCREEN_HEIGHT // 2 + 44, False)

    def draw_prediction_line(self, frame, pos_pelota, y_predicha, x_paleta_ia):
        """Guia educativa: linea desde la pelota hasta la vertical de la paleta IA en Y predicha."""
        if y_predicha is None or pos_pelota is None:
            return
        bx, by = int(pos_pelota[0]), int(pos_pelota[1])
        px = int(x_paleta_ia)
        py = int(max(0, min(settings.SCREEN_HEIGHT - 1, y_predicha)))
        cv2.line(frame, (bx, by), (px, py), (255, 255, 0), 2, cv2.LINE_AA)
        cv2.circle(frame, (px, py), 9, (255, 255, 0), 2, cv2.LINE_AA)

    def draw_edu_panel(self, frame, info):
        """
        Panel educativo ampliado:
        - Muestra error de IA, mezcla simple/pred.
        - Y predicha y Y de la pelota.
        - Cuadro mas grande y texto mayor, todo en ASCII.
        """
        x0, y0, w, h = 18, 18, 420, 170
        # Fondo opaco para maxima legibilidad
        cv2.rectangle(frame, (x0, y0), (x0 + w, y0 + h), (10, 10, 10), -1)
        cv2.rectangle(frame, (x0, y0), (x0 + w, y0 + h), (90, 90, 90), 2)

        def put(linea, texto, escala=0.8, grosor=2, dy=28):
            cv2.putText(
                frame, texto, (x0 + 14, y0 + 32 + dy * linea),
                settings.FONT, escala, (255, 255, 255), grosor, cv2.LINE_AA
            )

        err = max(0, min(100, int(round(float(info.get("error_rate", 0.0)) * 100))))
        mix = max(0, min(100, int(round(float(info.get("mix", 0.0)) * 100))))
        adv = info.get("adv_pred_y", None)
        by = info.get("ball_y", None)

        put(0, "Panel educativo", escala=0.95, grosor=2)
        put(1, f"Error IA: {err} %")
        put(2, f"Mezcla predictiva: {mix} %")
        if adv is not None:
            put(3, f"Y predicha: {int(adv)} px")
        if by is not None:
            put(4, f"Y pelota: {int(by)} px")

    # ----- util -----
    def _texto_centrado(self, frame, texto, y, grande):
        escala = 2.4 if grande else 1.2
        grosor = 4 if grande else 2
        (w, _), _ = cv2.getTextSize(texto, settings.FONT, escala, grosor)
        x = (settings.SCREEN_WIDTH - w) // 2
        cv2.putText(frame, texto, (x, y), settings.FONT, escala, (255, 255, 255), grosor, cv2.LINE_AA)