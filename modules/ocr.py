import cv2
import numpy as np
import pytesseract
import logging
import os
import time

from modules.config import TESSERACT_CMD

logger = logging.getLogger(__name__)

# Configurar la ruta del binario de Tesseract
pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
if not os.path.exists(TESSERACT_CMD):
    logger.warning(f"Tesseract no encontrado en '{TESSERACT_CMD}' — OCR retornará cadena vacía")


def extract_text(frame_bytes: bytes) -> str:
    start = time.time()

    nparr = np.frombuffer(frame_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        logger.warning("No se pudo decodificar la imagen para OCR")
        return ""

    # Preprocesamiento para mejorar detección de texto
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    processed = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11, 2
    )

    # Intentar con español; si tessdata/spa no está instalado, caer a inglés; si falla todo, retornar ""
    text = ""
    for lang in ("spa", "eng"):
        try:
            text = pytesseract.image_to_string(processed, lang=lang).strip()
            break
        except Exception as e:
            logger.warning(f"OCR falló con lang='{lang}': {e}")

    latency_ms = (time.time() - start) * 1000
    logger.info(f"Latencia OCR: {latency_ms:.1f}ms — texto detectado: {bool(text)}")

    return text if text else ""
