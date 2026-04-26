import io
import time
import logging
import threading

logger = logging.getLogger(__name__)

# Intentar importar pygame; si falla, usar playsound como fallback
try:
    import pygame
    _BACKEND = "pygame"
except ImportError:
    pygame = None
    try:
        from playsound import playsound as _playsound
        _BACKEND = "playsound"
    except ImportError:
        _playsound = None
        _BACKEND = "none"
    logger.warning(f"pygame no disponible. Backend de audio: {_BACKEND}")


class AudioPlayer:
    def __init__(self):
        self._playing = False
        # Lock para proteger _playing de accesos concurrentes desde consume_output y callback STT
        self._lock = threading.Lock()

        if _BACKEND == "pygame":
            pygame.mixer.init(frequency=44100)
            logger.info("pygame.mixer inicializado a 44100 Hz")
        elif _BACKEND == "none":
            logger.error("No hay backend de audio disponible (pygame ni playsound)")

    def play(self, audio_bytes: bytes) -> None:
        if not audio_bytes:
            logger.warning("Se recibió audio vacío, reproducción cancelada")
            return

        # Adquirir lock para leer y setear _playing de forma atómica
        with self._lock:
            if self._playing:
                logger.info("Audio en curso — descartando nueva reproducción")
                return
            self._playing = True

        start = time.time()
        logger.info("Iniciando reproducción de audio")
        try:
            if _BACKEND == "pygame":
                self._play_pygame(audio_bytes)
            elif _BACKEND == "playsound":
                self._play_playsound(audio_bytes)
            else:
                logger.error("Sin backend de audio disponible — audio descartado")
        finally:
            duration_ms = (time.time() - start) * 1000
            self._playing = False
            logger.info(f"Reproducción finalizada — duración: {duration_ms:.1f}ms")

    def _play_pygame(self, audio_bytes: bytes) -> None:
        buf = io.BytesIO(audio_bytes)
        pygame.mixer.music.load(buf)
        pygame.mixer.music.play()
        # Bloquear hasta que termine para evitar overlap
        while pygame.mixer.music.get_busy():
            time.sleep(0.05)

    def _play_playsound(self, audio_bytes: bytes) -> None:
        # playsound no soporta BytesIO — si se llega aquí, la demo necesita pygame
        logger.error("playsound no soporta reproducción desde memoria; instalar pygame")

    def is_playing(self) -> bool:
        return self._playing
