import os
from dotenv import load_dotenv
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cargar variables desde .env
load_dotenv()

# Evitar que GOOGLE_API_KEY del entorno del sistema sobreescriba GEMINI_API_KEY
# El SDK de Google usa GOOGLE_API_KEY como key alternativa, lo que puede apuntar a una key distinta
os.environ.pop("GOOGLE_API_KEY", None)

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
TESSERACT_CMD = get_env_variable("TESSERACT_CMD", r"C:\Program Files\Tesseract-OCR\tesseract.exe")

# Validación de arranque — fallar rápido antes de conectar cualquier API
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY no está definida en .env — el sistema no puede arrancar")
if GOOGLE_APPLICATION_CREDENTIALS and not os.path.exists(GOOGLE_APPLICATION_CREDENTIALS):
    raise RuntimeError(f"GOOGLE_APPLICATION_CREDENTIALS apunta a un archivo inexistente: {GOOGLE_APPLICATION_CREDENTIALS}")
