import logging
import time
from typing import Optional

try:
    from ultralytics import YOLO
except Exception:
    YOLO = None

from modules.processing.hazard_rules import HazardEvent, classify_hazard

logger = logging.getLogger(__name__)


class HazardDetector:
    def __init__(self, enabled: bool = True, model_name: str = "yolov8n.pt", cooldown_seconds: float = 6.0):
        self.enabled = enabled
        self.cooldown_seconds = cooldown_seconds
        self._last_emitted: dict[str, float] = {}
        self._model = None

        if self.enabled and YOLO is not None:
            try:
                self._model = YOLO(model_name)
                logger.info("Modelo YOLO cargado para deteccion de peligros")
            except Exception as e:
                logger.warning(f"No se pudo cargar YOLO ({model_name}): {e}")
        elif self.enabled:
            logger.warning("ultralytics no disponible: solo se aplicaran reglas OCR")

    def _cooldown_ok(self, key: str) -> bool:
        now = time.time()
        prev = self._last_emitted.get(key, 0.0)
        if now - prev < self.cooldown_seconds:
            return False
        self._last_emitted[key] = now
        return True

    def detect(self, frame: bytes, ocr_text: str) -> Optional[HazardEvent]:
        if not self.enabled:
            return None

        evt = classify_hazard(ocr_text=ocr_text, object_name=None, confidence=0.0)
        if evt and self._cooldown_ok(evt.key):
            return evt

        if self._model is None or not frame:
            return None

        try:
            results = self._model(frame, verbose=False)
            if not results:
                return None
            result = results[0]
            names = result.names
            for box in result.boxes:
                cls_id = int(box.cls[0].item())
                conf = float(box.conf[0].item())
                obj_name = names.get(cls_id, str(cls_id))
                evt = classify_hazard(ocr_text="", object_name=obj_name, confidence=conf)
                if evt and self._cooldown_ok(evt.key):
                    return evt
        except Exception as e:
            logger.warning(f"Fallo en deteccion de objetos: {e}")

        return None

