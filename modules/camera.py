import cv2
import logging
from modules.config import CAMERA_INDEX

logger = logging.getLogger(__name__)


class Camera:
    def __init__(self):
        self.cap = None

    def start(self):
        self.cap = cv2.VideoCapture(CAMERA_INDEX)
        if not self.cap.isOpened():
            raise RuntimeError(f"No se pudo abrir la cámara con índice {CAMERA_INDEX}. "
                               "Verifica que la cámara esté conectada y que CAMERA_INDEX sea correcto.")
        logger.info(f"Cámara {CAMERA_INDEX} iniciada correctamente.")

    def capture_frame(self):
        """Captura un frame de la cámara. Retorna el frame o None si falla."""
        if self.cap is None or not self.cap.isOpened():
            logger.warning("Cámara no disponible.")
            return None
        ret, frame = self.cap.read()
        if not ret:
            logger.warning("No se pudo capturar frame de la cámara.")
            return None
        return frame

    def stop(self):
        if self.cap:
            self.cap.release()
            logger.info("Cámara liberada.")
