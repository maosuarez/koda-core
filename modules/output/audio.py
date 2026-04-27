import io
import time
import logging
import threading
import queue
from dataclasses import dataclass
from typing import Optional

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


@dataclass
class AudioTask:
    audio_bytes: bytes
    priority: int = 2
    interrupt: bool = False
    ttl_seconds: float = 5.0
    created_at: float = 0.0
    resume_on_interrupt: bool = False


class AudioPlayer:
    def __init__(self, max_queue: int = 12, interruptions_enabled: bool = True, drop_expired: bool = True):
        self._playing = False
        self._lock = threading.Lock()
        self._task_queue: queue.PriorityQueue[tuple[int, float, AudioTask]] = queue.PriorityQueue(maxsize=max_queue)
        self._resume_stack: list[AudioTask] = []
        self._interruptions_enabled = interruptions_enabled
        self._drop_expired = drop_expired
        self._current_task: Optional[AudioTask] = None
        self._seq = 0
        self._running = True
        self._worker = threading.Thread(target=self._consume_loop, daemon=True)

        if _BACKEND == "pygame":
            pygame.mixer.init(frequency=44100)
            logger.info("pygame.mixer inicializado a 44100 Hz")
        elif _BACKEND == "none":
            logger.error("No hay backend de audio disponible (pygame ni playsound)")

        self._worker.start()

    def enqueue(self, audio_bytes: bytes, priority: int = 2, interrupt: bool = False, ttl_seconds: float = 5.0, resume_on_interrupt: bool = False) -> None:
        if not audio_bytes:
            logger.warning("Se recibio audio vacio, encolado cancelado")
            return

        task = AudioTask(
            audio_bytes=audio_bytes,
            priority=priority,
            interrupt=interrupt,
            ttl_seconds=ttl_seconds,
            created_at=time.time(),
            resume_on_interrupt=resume_on_interrupt,
        )

        with self._lock:
            if self._interruptions_enabled and interrupt and self._playing and self._current_task is not None:
                if task.priority < self._current_task.priority:
                    if self._current_task.resume_on_interrupt:
                        self._resume_stack.append(self._current_task)
                    self.stop_current()
            try:
                self._seq += 1
                self._task_queue.put_nowait((task.priority, self._seq, task))
            except queue.Full:
                logger.warning("Cola de audio llena; se descarta nuevo audio")

    def play(self, audio_bytes: bytes) -> None:
        # Compatibilidad retro para llamadas previas.
        self.enqueue(audio_bytes, priority=2, interrupt=False)

    def _is_expired(self, task: AudioTask) -> bool:
        return (time.time() - task.created_at) > task.ttl_seconds

    def _consume_loop(self) -> None:
        while self._running:
            try:
                _, _, task = self._task_queue.get(timeout=0.2)
            except queue.Empty:
                continue

            if self._drop_expired and self._is_expired(task):
                logger.info("Audio expirado por TTL; descartado")
                continue

            self._play_task(task)

            if not self._playing and self._resume_stack:
                resumed = self._resume_stack.pop()
                if not self._drop_expired or not self._is_expired(resumed):
                    self.enqueue(
                        resumed.audio_bytes,
                        priority=resumed.priority,
                        interrupt=False,
                        ttl_seconds=resumed.ttl_seconds,
                        resume_on_interrupt=False,
                    )

    def _play_task(self, task: AudioTask) -> None:
        start = time.time()
        with self._lock:
            self._playing = True
            self._current_task = task

        try:
            if _BACKEND == "pygame":
                self._play_pygame(task.audio_bytes)
            elif _BACKEND == "playsound":
                self._play_playsound(task.audio_bytes)
            else:
                logger.error("Sin backend de audio disponible; audio descartado")
        finally:
            duration_ms = (time.time() - start) * 1000
            with self._lock:
                self._playing = False
                self._current_task = None
            logger.info(f"Reproduccion finalizada - duracion: {duration_ms:.1f}ms")

    def stop_current(self) -> None:
        if _BACKEND == "pygame":
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass

    def clear_queue(self) -> None:
        while not self._task_queue.empty():
            try:
                self._task_queue.get_nowait()
            except queue.Empty:
                break
        self._resume_stack.clear()
        logger.info("Cola de audio vaciada")

    def _play_pygame(self, audio_bytes: bytes) -> None:
        buf = io.BytesIO(audio_bytes)
        pygame.mixer.music.load(buf, 'audio.mp3')
        pygame.mixer.music.play()
        # Bloquear hasta que termine para evitar overlap
        while pygame.mixer.music.get_busy():
            time.sleep(0.05)

    def _play_playsound(self, audio_bytes: bytes) -> None:
        # playsound no soporta BytesIO — si se llega aquí, la demo necesita pygame
        logger.error("playsound no soporta reproducción desde memoria; instalar pygame")

    def is_playing(self) -> bool:
        with self._lock:
            return self._playing

    def shutdown(self) -> None:
        self._running = False
        if self._worker:
            self._worker.join(timeout=1.0)
