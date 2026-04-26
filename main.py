import logging
import time
import queue
import threading

from modules.processing import Processor
from modules.camera import Camera
from modules.ocr import extract_text
from modules.audio import play_audio
from modules.config import FRAME_RATE

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("Main")


def _audio_consumer(processor: Processor):
    """Hilo que consume audio de la cola de salida y lo reproduce."""
    while processor.running:
        try:
            audio = processor.output_queue.get(timeout=1)
            play_audio(audio)
            processor.output_queue.task_done()
        except queue.Empty:
            continue


def main():
    logger.info("Iniciando KODA Core...")

    processor = Processor()
    processor.start()

    camera = Camera()
    camera.start()

    audio_thread = threading.Thread(target=_audio_consumer, args=(processor,), daemon=True)
    audio_thread.start()

    frame_interval = 1.0 / FRAME_RATE
    logger.info(f"Capturando a {FRAME_RATE} FPS. Presiona Ctrl+C para detener.")

    try:
        while True:
            tick = time.time()

            frame = camera.capture_frame()
            if frame is not None:
                ocr_text = extract_text(frame)
                processor.input_queue.put({'frame': frame, 'ocr_text': ocr_text})

            elapsed = time.time() - tick
            sleep_time = frame_interval - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

    except KeyboardInterrupt:
        logger.info("Deteniendo sistema...")
        processor.stop()
        camera.stop()


if __name__ == "__main__":
    main()
