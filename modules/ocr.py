import platform
import cv2
import pytesseract
import logging

logger = logging.getLogger(__name__)

# En Windows, Tesseract no queda en el PATH automáticamente
if platform.system() == 'Windows':
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


def extract_text(frame) -> str:
    """Extrae texto visible en un frame con preprocesamiento para mejorar la detección."""
    try:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # Umbralización Otsu para mejorar contraste del texto
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        text = pytesseract.image_to_string(thresh, lang='spa').strip()
        if text:
            logger.info(f"OCR detectó texto: {text[:60]}...")
        return text
    except Exception as e:
        logger.error(f"Error en OCR: {e}")
        return ""
