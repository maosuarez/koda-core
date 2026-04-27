import cv2
import threading
import logging
import time
from modules import config

logger = logging.getLogger(__name__)


class CameraCapture:
    def __init__(self):
        self._cap = None
        self._thread = None
        self._running = False
        self._frame: bytes | None = None
        self._lock = threading.Lock()

    def start(self):
        self._cap = cv2.VideoCapture(config.CAMERA_INDEX)
        if not self._cap.isOpened():
            raise RuntimeError(
                f"No se pudo abrir la cámara en índice {config.CAMERA_INDEX}. "
                "Verifica que está conectada y no está en uso."
            )
        self._running = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()
        logger.info(f"Captura de cámara iniciada en índice {config.CAMERA_INDEX}")

    def _capture_loop(self):
        while self._running:
            ret, frame = self._cap.read()
            if not ret:
                logger.warning("No se pudo leer frame de la cámara")
                time.sleep(0.1)
                continue
            _, buffer = cv2.imencode(".jpg", frame)
            with self._lock:
                self._frame = buffer.tobytes()
            # Limitar captura a ~15 FPS para no saturar CPU
            time.sleep(1 / 15)

    def get_frame(self) -> bytes | None:
        with self._lock:
            return self._frame

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        if self._cap:
            self._cap.release()
        logger.info("Captura de cámara detenida")
