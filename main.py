import queue
import signal
import threading
import time
import logging

# Importar pygame aquí para el shutdown limpio
try:
    import pygame
except ImportError:
    pygame = None

from modules.config import GEMINI_API_KEY  # fuerza validación al arrancar
from modules.camera import CameraCapture
from modules.audio import AudioPlayer
from modules.gemini_client import get_conversation_response
from modules.tts_client import synthesize_speech
from modules.stt_client import SpeechToTextClient
from modules.ocr import extract_text
from modules.processing import Processor

# Logging centralizado — nivel INFO por defecto
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("Main")

# Flag compartido para el shutdown limpio
running = True


def main():
    global running

    logger.info("Iniciando KODA Core...")

    # --- Instanciación de módulos en orden de dependencia ---
    camera = CameraCapture()
    player = AudioPlayer()
    processor = Processor()

    # --- Hilo consumidor de audio (output_queue del Processor) ---
    def consume_output():
        # Usa el flag 'running' para terminar limpiamente en shutdown
        while running:
            try:
                audio_bytes = processor.output_queue.get(timeout=0.5)
                player.play(audio_bytes)
            except queue.Empty:
                continue

    threading.Thread(target=consume_output, daemon=True).start()
    logger.info("Hilo consumidor de audio iniciado")

    # --- Callback STT: responde preguntas del usuario con contexto visual actual ---
    def on_speech(transcript: str):
        logger.info(f"Pregunta del usuario: '{transcript}'")
        # Leer last_description del Processor — contexto visual aproximado sin sincronización rígida
        description = get_conversation_response(transcript, processor.last_description)
        if description.strip():
            audio = synthesize_speech(description)
            player.play(audio)

    # --- Iniciar subsistemas ---
    camera.start()
    processor.start()

    stt = SpeechToTextClient()
    stt.start(callback=on_speech)
    logger.info("Sistema KODA listo — escuchando")

    # --- Shutdown limpio con Ctrl+C ---
    def shutdown_handler(sig, frame):
        global running
        logger.info("Señal de interrupción recibida — apagando sistema...")
        running = False
        camera.stop()
        stt.stop()
        processor.stop()
        if pygame is not None:
            pygame.quit()

    signal.signal(signal.SIGINT, shutdown_handler)

    # --- Loop principal a ~1 FPS: captura frame → OCR → cola del Processor ---
    while running:
        frame = camera.get_frame()
        if frame is not None:
            try:
                ocr_text = extract_text(frame)
            except Exception as e:
                logger.warning(f"OCR falló — continuando sin texto: {e}")
                ocr_text = ""
            item = {"frame": frame, "ocr_text": ocr_text, "t0": time.time()}
            # put_nowait descarta si la cola está llena — preferimos perder un frame que bloquear
            try:
                processor.input_queue.put_nowait(item)
            except Exception:
                logger.debug("Cola de entrada llena — frame descartado")
        time.sleep(1.0)

    logger.info("KODA Core detenido.")


if __name__ == "__main__":
    main()
