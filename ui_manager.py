# ui_manager.py
# Interfaz del juego y panel educativo (todo en español y ASCII)

import cv2
import settings


class UIManager:
    def draw_center_line(self, frame):
        xmid = settings.SCREEN_WIDTH // 2
        for y in range(0, settings.SCREEN_HEIGHT, 40):
            cv2.line(frame, (xmid, y), (xmid, y + 20), (255, 255, 255), 2)

    def draw_scores(self, frame, score_ai, score_player):
        cv2.putText(frame, str(score_ai), (settings.SCREEN_WIDTH // 4, 100),
                    settings.FONT, 2, (255, 100, 100), 3, cv2.LINE_AA)
        cv2.putText(frame, str(score_player),
                    (settings.SCREEN_WIDTH * 3 // 4 - 60, 100),
                    settings.FONT, 2, (100, 255, 100), 3, cv2.LINE_AA)

    def draw_menu(self, frame, subtitle=""):
        self._text_center(frame, "HAND PONG", settings.SCREEN_HEIGHT // 2 - 100, True)
        if subtitle:
            self._text_center(frame, subtitle, settings.SCREEN_HEIGHT // 2 - 40, False)
        self._text_center(frame, "Presiona ESPACIO para comenzar", settings.SCREEN_HEIGHT // 2 + 60, False)

    def draw_footer_help(self, frame):
        text = "ESPACIO: jugar/pausar | R: reiniciar | ESC: salir | H: esqueleto | G: pantalla completa | O: panel educativo"
        (tw, _), _ = cv2.getTextSize(text, settings.FONT, 0.6, 1)
        x = (settings.SCREEN_WIDTH - tw) // 2
        y = settings.SCREEN_HEIGHT - 15
        cv2.putText(frame, text, (x, y), settings.FONT, 0.6, (200, 200, 200), 1, cv2.LINE_AA)

    def draw_center_message(self, frame, msg, submsg=""):
        self._text_center(frame, msg, settings.SCREEN_HEIGHT // 2 - 40, True)
        if submsg:
            self._text_center(frame, submsg, settings.SCREEN_HEIGHT // 2 + 40, False)

    def draw_prediction_line(self, frame, ball_pos, pred_y, ai_x):
        if pred_y is None:
            return
        bx, by = int(ball_pos[0]), int(ball_pos[1])
        px = int(ai_x)
        py = int(pred_y)
        cv2.line(frame, (bx, by), (px, py), (255, 255, 0), 2, cv2.LINE_AA)
        cv2.circle(frame, (px, py), 8, (255, 255, 0), 2, cv2.LINE_AA)

    def draw_edu_panel(self, frame, info):
        x0, y0, w, h = 20, 20, 320, 110
        cv2.rectangle(frame, (x0, y0), (x0 + w, y0 + h), (0, 0, 0), -1)
        cv2.rectangle(frame, (x0, y0), (x0 + w, y0 + h), (70, 70, 70), 2)

        def put(line, text):
            cv2.putText(frame, text, (x0 + 12, y0 + 26 + 22 * line),
                        settings.FONT, 0.6, (255, 255, 255), 1, cv2.LINE_AA)

        err = int(info.get("error_rate", 0.0) * 100)
        mix = int(info.get("mix", 0.0) * 100)
        adv = info.get("adv_pred_y", None)
        put(0, "Panel educativo")
        put(1, f"Error IA: {err}%")
        put(2, f"Mezcla predictiva: {mix}%")
        if adv:
            put(3, f"Y predicha: {int(adv)} px")

    def _text_center(self, frame, text, y, large):
        scale = 2 if large else 1
        thick = 3 if large else 2
        (w, _), _ = cv2.getTextSize(text, settings.FONT, scale, thick)
        x = (settings.SCREEN_WIDTH - w) // 2
        cv2.putText(frame, text, (x, y), settings.FONT, scale, (255, 255, 255), thick, cv2.LINE_AA)