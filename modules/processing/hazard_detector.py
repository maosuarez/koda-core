import logging
import time
from typing import Optional

import cv2
import numpy as np

try:
    from ultralytics import YOLO
except Exception:
    YOLO = None

from modules import config
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
                logger.info(f"YOLO listo — modelo: {model_name}")
            except Exception as e:
                logger.warning(f"No se pudo cargar YOLO ({model_name}): {e}")
        elif self.enabled:
            logger.warning("YOLO no disponible — no habrá detección visual de objetos (instala ultralytics)")

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
            nparr = np.frombuffer(frame, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is None:
                return None
            results = self._model(img, verbose=False)
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

    def get_visual_detections(self, frame: bytes) -> list[dict]:
        """Retorna todos los objetos detectados con bboxes y clasificación de proximidad."""
        _, detections = self.detect_with_visuals(frame, ocr_text="")
        return detections

    def detect_with_visuals(self, frame: bytes, ocr_text: str) -> tuple[Optional[HazardEvent], list[dict]]:
        """Corre YOLO una sola vez y retorna (peligro, detecciones). Evita doble pasada."""
        if not self.enabled:
            return None, []

        # Verificar peligro por OCR primero (rápido, sin YOLO)
        ocr_hazard = classify_hazard(ocr_text=ocr_text, object_name=None, confidence=0.0)
        ocr_evt = ocr_hazard if (ocr_hazard and self._cooldown_ok(ocr_hazard.key)) else None

        if self._model is None or not frame:
            return ocr_evt, []

        yolo_hazard: Optional[HazardEvent] = None
        detections: list[dict] = []

        try:
            nparr = np.frombuffer(frame, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is None:
                return ocr_evt, []
            results = self._model(img, verbose=False)
            if not results:
                return ocr_evt, []
            result = results[0]
            h, w = result.orig_shape
            frame_area = h * w
            names = result.names
            for box in result.boxes:
                conf = float(box.conf[0].item())
                cls_id = int(box.cls[0].item())
                obj_name = names.get(cls_id, str(cls_id))
                if yolo_hazard is None:
                    evt = classify_hazard(ocr_text="", object_name=obj_name, confidence=conf)
                    if evt and self._cooldown_ok(evt.key):
                        yolo_hazard = evt
                if conf >= 0.25:
                    xyxy = box.xyxy[0].tolist()
                    x1, y1, x2, y2 = xyxy
                    bbox_area = (x2 - x1) * (y2 - y1)
                    is_close = (bbox_area / frame_area) >= config.HAZARD_PROXIMITY_THRESHOLD
                    detections.append({
                        "xyxy": [int(x1), int(y1), int(x2), int(y2)],
                        "label": obj_name,
                        "conf": conf,
                        "is_close": is_close,
                    })
            logger.info(f"Detecciones visuales: {len(detections)} objetos — {[d['label'] for d in detections]}")
        except Exception as e:
            logger.warning(f"Fallo en deteccion YOLO: {e}")

        # OCR tiene prioridad sobre YOLO para peligros
        return ocr_evt or yolo_hazard, detections

