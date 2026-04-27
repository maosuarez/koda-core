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
from modules.push_to_talk import PushToTalkClient
from modules.ocr import extract_text
from modules.processing import Processor
from modules.navigation import NavigationClient

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
    nav = NavigationClient()

    # Event compartido: se setea cuando PTT está activo, se limpia al reanudar
    ptt_active = threading.Event()

    # Estado de navegación continua — dict simple, accedido desde PTT thread y nav_announcer
    nav_state = {
        "active": False,
        "steps": [],
        "index": 0,
        "destination": "",
    }

    # --- Hilo consumidor de audio (output_queue del Processor) ---
    def consume_output():
        # Usa el flag 'running' para terminar limpiamente en shutdown
        # Mientras PTT está activo, no reproducir audio del pipeline
        while running:
            if ptt_active.is_set():
                time.sleep(0.1)
                continue
            try:
                audio_bytes = processor.output_queue.get(timeout=0.5)
                player.play(audio_bytes)
            except queue.Empty:
                continue

    threading.Thread(target=consume_output, daemon=True).start()
    logger.info("Hilo consumidor de audio iniciado")

    # --- Helpers de navegación continua ---
    def get_nav_step() -> str:
        if nav_state["active"] and nav_state["index"] < len(nav_state["steps"]):
            return nav_state["steps"][nav_state["index"]]
        return ""

    def announce_nav_step() -> None:
        step = get_nav_step()
        if step:
            audio = synthesize_speech(step)
            player.play(audio)

    # Hilo que repite el paso actual cada 15s mientras navegación está activa
    def nav_announcer():
        last_t = 0.0
        while running:
            if nav_state["active"] and not ptt_active.is_set() and (time.time() - last_t) >= 15:
                announce_nav_step()
                last_t = time.time()
            time.sleep(1)

    threading.Thread(target=nav_announcer, daemon=True).start()
    logger.info("Hilo de anuncios de navegación iniciado")

    # --- Callback STT: navegación o descripción de escena según el transcript ---
    def on_speech(transcript: str):
        logger.info(f"Pregunta del usuario: '{transcript}'")
        if nav.is_navigation_query(transcript):
            response = nav.navigate_to(transcript)
        else:
            # Leer last_description del Processor — contexto visual aproximado sin sincronización rígida
            response = get_conversation_response(transcript, processor.last_description)
        if response.strip():
            audio = synthesize_speech(response)
            player.play(audio)

    # --- Callbacks separados para STT continuo y PTT ---
    def on_stt_speech(transcript: str):
        # El STT continuo ignora transcripts mientras PTT está activo
        if ptt_active.is_set():
            return
        on_speech(transcript)

    def on_ptt_speech(transcript: str):
        logger.info(f"PTT recibido: '{transcript}'")

        if nav_state["active"]:
            if nav.is_cancel_command(transcript):
                nav_state["active"] = False
                audio = synthesize_speech("Navegación cancelada.")
                player.play(audio)

            elif nav.is_next_step_command(transcript):
                nav_state["index"] += 1
                if nav_state["index"] >= len(nav_state["steps"]):
                    nav_state["active"] = False
                    audio = synthesize_speech("Has llegado a tu destino.")
                    player.play(audio)
                else:
                    announce_nav_step()

            else:
                # Pregunta durante navegación — contexto de ruta inyectado en scene_description
                step = get_nav_step()
                combined = f"{processor.last_description}\n[Navegación activa — paso actual]: {step}" if step else processor.last_description
                response = get_conversation_response(transcript, combined)
                if response.strip():
                    audio = synthesize_speech(response)
                    player.play(audio)

        elif nav.is_navigation_query(transcript):
            # Activar modo navegación continua
            steps = nav.start_navigation(transcript)
            nav_state.update({"active": True, "steps": steps, "index": 0, "destination": transcript})
            logger.info(f"Navegación iniciada hacia '{transcript}' — {len(steps)} pasos")
            announce_nav_step()

        else:
            # Pregunta normal sin navegación activa
            response = get_conversation_response(transcript, processor.last_description)
            if response.strip():
                audio = synthesize_speech(response)
                player.play(audio)

        ptt_active.clear()
        logger.info("PTT — pipeline reanudado")

    # --- Iniciar subsistemas ---
    camera.start()
    processor.start()

    stt = SpeechToTextClient()
    stt.start(callback=on_stt_speech)

    ptt = PushToTalkClient(
        ptt_active=ptt_active,
        player=player,
        processor_output_queue=processor.output_queue,
    )
    ptt.start(callback=on_ptt_speech)
    logger.info("Push-to-talk iniciado — mantén Enter para hablar")

    logger.info("Sistema KODA listo — escuchando")

    # --- Shutdown limpio con Ctrl+C ---
    def shutdown_handler(sig, frame):
        global running
        logger.info("Señal de interrupción recibida — apagando sistema...")
        running = False
        camera.stop()
        stt.stop()
        ptt.stop()
        processor.stop()
        if pygame is not None:
            pygame.quit()

    signal.signal(signal.SIGINT, shutdown_handler)

    # --- Loop principal a ~1 FPS: captura frame → OCR → cola del Processor ---
    while running:
        # Pausar captura mientras PTT está activo — no enviar frames ni descripciones
        if ptt_active.is_set():
            time.sleep(0.1)
            continue
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
