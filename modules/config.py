import os
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()


def get_env_variable(key: str, default: str = None) -> str:
    value = os.getenv(key, default)
    if not value:
        logger.warning(f"La variable de entorno '{key}' no está definida.")
        return default
    return value


# Configuración centralizada
GEMINI_API_KEY = get_env_variable("GEMINI_API_KEY")
GOOGLE_APPLICATION_CREDENTIALS = get_env_variable("GOOGLE_APPLICATION_CREDENTIALS")
TTS_LANGUAGE_CODE = get_env_variable("TTS_LANGUAGE_CODE", "es-US")
TTS_VOICE_NAME = get_env_variable("TTS_VOICE_NAME", "es-US-Neural2-B")
CAMERA_INDEX = int(get_env_variable("CAMERA_INDEX", "0"))
FRAME_RATE = float(get_env_variable("FRAME_RATE", "1"))
