import io
import os
import tempfile
import logging
import pygame

logger = logging.getLogger(__name__)

_mixer_ready = False


def _ensure_mixer():
    global _mixer_ready
    if not _mixer_ready:
        try:
            pygame.mixer.init()
            _mixer_ready = True
        except Exception as e:
            logger.error(f"No se pudo inicializar pygame mixer: {e}")


def play_audio(audio_bytes: bytes):
    """Reproduce audio MP3 desde bytes usando pygame."""
    if not audio_bytes:
        logger.warning("play_audio recibió bytes vacíos, nada que reproducir.")
        return

    _ensure_mixer()
    if not _mixer_ready:
        logger.error("pygame mixer no disponible, no se puede reproducir audio.")
        return

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
            f.write(audio_bytes)
            tmp_path = f.name

        pygame.mixer.music.load(tmp_path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

    except Exception as e:
        logger.error(f"Error reproduciendo audio: {e}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
