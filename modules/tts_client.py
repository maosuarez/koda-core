import time
import logging
from google.cloud import texttospeech
from modules.config import TTS_LANGUAGE_CODE, TTS_VOICE_NAME

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = texttospeech.TextToSpeechClient()
    return _client


def synthesize_speech(text: str) -> bytes:
    """Convierte texto a audio con medición de latencia."""
    start_time = time.time()

    try:
        synthesis_input = texttospeech.SynthesisInput(text=text)
        voice = texttospeech.VoiceSelectionParams(
            language_code=TTS_LANGUAGE_CODE,
            name=TTS_VOICE_NAME,
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )

        response = _get_client().synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )

        latency = time.time() - start_time
        logger.info(f"Latencia TTS: {latency:.4f}s")
        return response.audio_content

    except Exception as e:
        logger.error(f"Error en TTS: {e}")
        return b""
