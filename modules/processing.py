import threading
import queue
import time
import logging
from modules.output.gemini_client import get_scene_description
from modules.output.tts_client import synthesize_speech

# Configurar logging según convenciones
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Processor")

class Processor:
    def __init__(self):
        # Colas acotadas: descartar entradas viejas si el procesador no da abasto
        self.input_queue = queue.Queue(maxsize=2)
        self.output_queue = queue.Queue(maxsize=2)
        self.running = True
        self.thread = None
        # Última descripción generada — leída por el callback STT para contexto visual
        self.last_description: str = ""

    def start(self):
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        logger.info("Procesador de puente iniciado.")

    def _run(self):
        while self.running:
            try:
                # Leer frame + OCR de entrada (incluye t0 para latencia E2E real)
                data = self.input_queue.get(timeout=1)
                try:
                    # Guard: descartar si no hay frame válido
                    if data.get('frame') is None:
                        logger.warning("Frame vacío recibido — descartando")
                        continue

                    # t0 fue registrado en el momento de captura del frame
                    start_e2e = data['t0']

                    # Procesar con Gemini (ya mide su propia latencia)
                    description = get_scene_description(data['frame'], data['ocr_text'])

                    # Actualizar descripción compartida antes del guard de vacío
                    if description.strip():
                        self.last_description = description

                    # Guard: descartar si Gemini no devolvió texto
                    if not description.strip():
                        logger.warning("Descripción vacía de Gemini — descartando")
                        continue

                    # Sintetizar con TTS (ya mide su propia latencia)
                    audio = synthesize_speech(description)

                    # put_nowait: si el consumidor se cuelga no bloqueamos el Processor
                    try:
                        self.output_queue.put_nowait(audio)
                    except queue.Full:
                        logger.warning("Cola de salida llena — descartando audio de escena")

                    # Latencia E2E real: desde captura del frame hasta audio listo
                    logger.info(f"Latencia E2E real: {(time.time() - start_e2e)*1000:.0f}ms")

                finally:
                    # task_done siempre se ejecuta, incluso si hay excepción en el procesamiento
                    self.input_queue.task_done()

            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error crítico en procesamiento: {e}")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
