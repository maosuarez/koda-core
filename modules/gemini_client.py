import time
import logging
import google.generativeai as genai
from modules.config import GEMINI_API_KEY
from modules.prompts import SCENE_DESCRIPTION_PROMPT

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurar Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

def get_scene_description(image_frame, ocr_text: str = "") -> str:
    """Obtiene descripción de la escena con medición de latencia."""
    start_time = time.time()
    
    try:
        prompt = SCENE_DESCRIPTION_PROMPT.format(ocr_text=ocr_text)
        # Aquí iría la llamada real con la imagen
        # response = model.generate_content([prompt, image_frame])
        # description = response.text
        
        # Simulación de respuesta para estructurar
        description = "Obstáculo detectado: silla en el camino."
        
        end_time = time.time()
        logger.info(f"Latencia Gemini: {end_time - start_time:.4f} segundos")
        return description
        
    except Exception as e:
        logger.error(f"Error en Gemini: {e}")
        return "No pude analizar la escena."
