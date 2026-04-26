import time
import logging
from google.cloud import texttospeech
from modules.config import TTS_LANGUAGE_CODE, TTS_VOICE_NAME

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = texttospeech.TextToSpeechClient()

def synthesize_speech(text: str) -> bytes:
    """Convierte texto a audio con medición de latencia."""
    start_time = time.time()
    
    try:
        synthesis_input = texttospeech.SynthesisInput(text=text)
        voice = texttospeech.VoiceSelectionParams(
            language_code=TTS_LANGUAGE_CODE,
            name=TTS_VOICE_NAME
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )
        
        response = client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )
        
        end_time = time.time()
        logger.info(f"Latencia TTS: {end_time - start_time:.4f} segundos")
        return response.audio_content
        
    except Exception as e:
        logger.error(f"Error en TTS: {e}")
        return b""
