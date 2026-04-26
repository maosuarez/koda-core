import threading
import queue
import time
import logging
from modules.gemini_client import get_scene_description
from modules.tts_client import synthesize_speech

# Configurar logging según convenciones
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Processor")

class Processor:
    def __init__(self):
        # Desacoplamiento total usando colas
        self.input_queue = queue.Queue()  # Nicolás pone aquí: {'frame': ..., 'ocr_text': ...}
        self.output_queue = queue.Queue() # Aquí ponemos el audio resultante para Thomas
        self.running = True
        self.thread = None

    def start(self):
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        logger.info("Procesador de puente iniciado.")

    def _run(self):
        while self.running:
            try:
                # Leer frame + OCR de entrada
                data = self.input_queue.get(timeout=1)
                start_e2e = time.time()
                
                # Procesar con Gemini (ya mide su propia latencia)
                description = get_scene_description(data['frame'], data['ocr_text'])
                
                # Sintetizar con TTS (ya mide su propia latencia)
                audio = synthesize_speech(description)
                
                # Poner en cola de salida para Thomas
                self.output_queue.put(audio)
                
                # Medición de latencia E2E
                total_latency = time.time() - start_e2e
                logger.info(f"Latencia E2E Total del puente: {total_latency:.4f}s")
                
                self.input_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error crítico en procesamiento: {e}")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
