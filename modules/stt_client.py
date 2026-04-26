import io
import wave
import logging
import pyaudio
from google.cloud import speech

logger = logging.getLogger(__name__)

RATE = 16000
CHANNELS = 1
CHUNK = 1024
RECORD_SECONDS = 4


def _record_audio() -> bytes:
    """Graba RECORD_SECONDS de audio desde el micrófono y retorna WAV en bytes."""
    p = pyaudio.PyAudio()
    frames = []

    stream = p.open(
        format=pyaudio.paInt16,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK,
    )

    logger.info(f"Grabando {RECORD_SECONDS} segundos de audio...")
    for _ in range(int(RATE / CHUNK * RECORD_SECONDS)):
        frames.append(stream.read(CHUNK))

    stream.stop_stream()
    stream.close()
    p.terminate()

    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))

    return buf.getvalue()


def listen_for_command() -> str:
    """Graba y transcribe un comando de voz del usuario. Retorna el texto o ''."""
    try:
        audio_bytes = _record_audio()

        client = speech.SpeechClient()
        audio = speech.RecognitionAudio(content=audio_bytes)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=RATE,
            language_code="es-CO",
        )

        response = client.recognize(config=config, audio=audio)
        if response.results:
            transcript = response.results[0].alternatives[0].transcript
            logger.info(f"STT detectó: {transcript}")
            return transcript

        logger.info("STT no detectó texto.")
        return ""

    except Exception as e:
        logger.error(f"Error en STT: {e}")
        return ""
