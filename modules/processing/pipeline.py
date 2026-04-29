import collections
import logging
import queue
import threading
import time

from modules.config import (
    HAZARD_COOLDOWN_SECONDS,
    HAZARD_DETECTION_ENABLED,
    HAZARD_MODEL_NAME,
)
from modules.output.gemini_client import get_scene_description
from modules.output.tts_client import synthesize_speech
from modules.processing.hazard_detector import HazardDetector
from modules.processing.hazard_rules import PRIORITY_NORMAL

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("Processor")


class Processor:
    def __init__(self):
        self.input_queue = queue.Queue(maxsize=2)
        self.output_queue = queue.Queue(maxsize=8)
        self.running = True
        self.thread = None
        self.last_description: str = ""
        self._last_detections: list = []
        self._detections_lock = threading.Lock()
        self._history: collections.deque = collections.deque(maxlen=3)
        self._mentioned_objects: dict[str, float] = {}
        self.hazard_detector = HazardDetector(
            enabled=HAZARD_DETECTION_ENABLED,
            model_name=HAZARD_MODEL_NAME,
            cooldown_seconds=HAZARD_COOLDOWN_SECONDS,
        )

    @property
    def last_detections(self) -> list:
        with self._detections_lock:
            return list(self._last_detections)

    def start(self):
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        logger.info("Procesador iniciado.")

    def _emit_audio_event(
        self,
        audio_bytes: bytes,
        priority: int,
        interrupt: bool,
        ttl_seconds: float = 5.0,
        resume_on_interrupt: bool = False,
    ):
        event = {
            "audio": audio_bytes,
            "priority": priority,
            "interrupt": interrupt,
            "ttl_seconds": ttl_seconds,
            "resume_on_interrupt": resume_on_interrupt,
        }
        try:
            self.output_queue.put_nowait(event)
        except queue.Full:
            logger.warning("Cola de salida llena; evento descartado")

    def _run(self):
        while self.running:
            try:
                data = self.input_queue.get(timeout=1)
                try:
                    frame = data.get("frame")
                    if frame is None:
                        logger.warning("Frame vacio; descartando")
                        continue

                    start_e2e = data["t0"]
                    ocr_text = data.get("ocr_text", "")

                    hazard, detections = self.hazard_detector.detect_with_visuals(frame, ocr_text)
                    with self._detections_lock:
                        self._last_detections = detections
                    if hazard:
                        hazard_audio = synthesize_speech(hazard.message)
                        self._emit_audio_event(
                            audio_bytes=hazard_audio,
                            priority=hazard.priority,
                            interrupt=hazard.interrupt,
                            ttl_seconds=hazard.ttl_seconds,
                            resume_on_interrupt=False,
                        )

                    now = time.time()
                    new_objects = [
                        d["label"] for d in detections
                        if now - self._mentioned_objects.get(d["label"], 0.0) >= 15.0
                    ]
                    for label in new_objects:
                        self._mentioned_objects[label] = now

                    description = get_scene_description(frame, ocr_text, list(self._history), new_objects or None)

                    if description.strip().upper() == "SKIP":
                        logger.info("Gemini — sin cambios significativos, frame omitido")
                        continue

                    if not description.strip():
                        logger.warning("Descripcion vacia de Gemini")
                        continue

                    self._history.append(description)
                    self.last_description = description
                    audio = synthesize_speech(description)

                    self._emit_audio_event(
                        audio_bytes=audio,
                        priority=PRIORITY_NORMAL,
                        interrupt=False,
                        ttl_seconds=4.0,
                        resume_on_interrupt=True,
                    )

                    logger.info(f"Latencia E2E: {(time.time() - start_e2e) * 1000:.0f}ms")
                finally:
                    self.input_queue.task_done()

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error critico en procesamiento: {e}")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)

