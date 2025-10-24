# ui_manager.py
# Interfaz visual rápida y clara para modo feria

import cv2
import settings

class UIManager:
    def draw_center_line(self, frame, dash=24, gap=20, thick=3):
        """Línea punteada central tipo Pong."""
        xmid = settings.SCREEN_WIDTH // 2
        s = settings.SCREEN_HEIGHT / float(settings.BASE_HEIGHT)
        d, g, t = int(dash * s), int(gap * s), int(thick * s)
        for y in range(0, settings.SCREEN_HEIGHT, d + g):
            cv2.line(frame, (xmid, y), (xmid, y + d), (255, 255, 255), t)

    def draw_scores(self, frame, score_ai, score_player):
        """Puntajes grandes en los bordes, más legibles."""
        # AI (izquierda)
        cv2.putText(
            frame, str(score_ai),
            (settings.SCREEN_WIDTH // 4, 120),
            settings.FONT, settings.FONT_SCALE_SCORE,
            settings.SCORE_COLOR_AI, settings.FONT_THICKNESS_SCORE, cv2.LINE_AA
        )
        # Player (derecha)
        cv2.putText(
            frame, str(score_player),
            (settings.SCREEN_WIDTH * 3 // 4 - 60, 120),
            settings.FONT, settings.FONT_SCALE_SCORE,
            settings.SCORE_COLOR_PLAYER, settings.FONT_THICKNESS_SCORE, cv2.LINE_AA
        )

    def draw_center_message(self, frame, message, sub_message=""):
        """Mensajes centrados para menú o pausa."""
        self._text_center(frame, message, settings.SCREEN_HEIGHT // 2 - 40, True)
        if sub_message:
            self._text_center(frame, sub_message, settings.SCREEN_HEIGHT // 2 + 40, False)

    def draw_menu(self, frame, subtitle=""):
        """Pantalla de inicio."""
        self._text_center(frame, "HAND PONG", settings.SCREEN_HEIGHT // 2 - 100, True)
        if subtitle:
            self._text_center(frame, subtitle, settings.SCREEN_HEIGHT // 2 - 40, False)
        self._text_center(frame, "Presiona ESPACIO para comenzar", settings.SCREEN_HEIGHT // 2 + 60, False)

        # Tips educativos
        y = settings.SCREEN_HEIGHT - 100
        for tip in settings.EDU_TIPS:
            self._text_center(frame, tip, y, False)
            y += 25

    def draw_footer_help(self, frame):
        """Controles del jugador en la parte inferior."""
        text = "ESPACIO: jugar/pausar | R: reiniciar | ESC: salir | H: esqueleto | G: pantalla completa"
        scale = 0.8
        (tw, _), _ = cv2.getTextSize(text, settings.FONT, scale, 1)
        x = (settings.SCREEN_WIDTH - tw) // 2
        y = settings.SCREEN_HEIGHT - 15
        cv2.putText(frame, text, (x, y), settings.FONT, scale, (200, 200, 200), 1, cv2.LINE_AA)

    def _text_center(self, frame, text, y, large):
        """Función auxiliar para centrar texto."""
        scale = settings.FONT_SCALE_SCORE if large else settings.FONT_SCALE_MSG
        thick = settings.FONT_THICKNESS_SCORE if large else settings.FONT_THICKNESS_MSG
        (w, _), _ = cv2.getTextSize(text, settings.FONT, scale, thick)
        x = (settings.SCREEN_WIDTH - w) // 2
        cv2.putText(frame, text, (x, y), settings.FONT, scale, settings.MSG_COLOR, thick, cv2.LINE_AA)