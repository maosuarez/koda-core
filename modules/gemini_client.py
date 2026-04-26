import cv2
import time
import logging
import PIL.Image
from google import genai
from modules.config import GEMINI_API_KEY
from modules.prompts import SCENE_DESCRIPTION_PROMPT

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client


def get_scene_description(image_frame, ocr_text: str = "") -> str:
    """Envía el frame a Gemini 2.5 Flash y retorna descripción de la escena."""
    start_time = time.time()

    try:
        frame_rgb = cv2.cvtColor(image_frame, cv2.COLOR_BGR2RGB)
        pil_image = PIL.Image.fromarray(frame_rgb)

        prompt = SCENE_DESCRIPTION_PROMPT.format(ocr_text=ocr_text)

        response = _get_client().models.generate_content(
            model='gemini-2.5-flash',
            contents=[prompt, pil_image],
        )
        description = response.text

        latency = time.time() - start_time
        logger.info(f"Latencia Gemini: {latency:.4f}s")
        return description

    except Exception as e:
        logger.error(f"Error en Gemini: {e}")
        return "No pude analizar la escena."
