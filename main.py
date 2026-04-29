import collections
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

import cv2
import numpy as np

from modules.config import (
    GEMINI_API_KEY,
    AUDIO_INTERRUPTIONS_ENABLED,
    AUDIO_QUEUE_MAXSIZE,
    AUDIO_DROP_EXPIRED,
    FRAME_SIMILARITY_THRESHOLD_STILL,
    FRAME_SIMILARITY_THRESHOLD_MOVING,
    FRAME_MOTION_DETECT_THRESHOLD,
)
from modules.input.camera import CameraCapture
from modules.output.audio import AudioPlayer
from modules.output.gemini_client import get_conversation_response
from modules.output.tts_client import synthesize_speech
from modules.input.stt_client import SpeechToTextClient
from modules.input.ocr import extract_text
from modules.processing.pipeline import Processor
from modules.push_to_talk import PushToTalkClient
from modules.navigation import NavigationClient

# Logging centralizado — nivel INFO por defecto
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("Main")

# Flag compartido para el shutdown limpio
running = True


def _frame_similarity_score(frame_a: bytes, frame_b: bytes) -> float:
    """Retorna score de similitud 0.0-1.0 entre dos frames JPEG. 1.0 = idénticos."""
    try:
        arr_a = np.frombuffer(frame_a, np.uint8)
        arr_b = np.frombuffer(frame_b, np.uint8)
        img_a = cv2.imdecode(arr_a, cv2.IMREAD_GRAYSCALE)
        img_b = cv2.imdecode(arr_b, cv2.IMREAD_GRAYSCALE)
        if img_a is None or img_b is None:
            return 0.0
        img_a = cv2.resize(img_a, (64, 64))
        img_b = cv2.resize(img_b, (64, 64))
        diff = cv2.absdiff(img_a, img_b)
        return 1.0 - (diff.mean() / 255.0)
    except Exception:
        return 0.0


def main():
    global running

    logger.info("Iniciando KODA Core...")

    # --- Instanciación de módulos en orden de dependencia ---
    camera = CameraCapture()
    player = AudioPlayer(
        max_queue=AUDIO_QUEUE_MAXSIZE,
        interruptions_enabled=AUDIO_INTERRUPTIONS_ENABLED,
        drop_expired=AUDIO_DROP_EXPIRED,
    )
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
        "last_announced": 0.0,
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
                event = processor.output_queue.get(timeout=0.5)
                if isinstance(event, dict):
                    player.enqueue(
                        event.get("audio", b""),
                        priority=event.get("priority", 2),
                        interrupt=event.get("interrupt", False),
                        ttl_seconds=event.get("ttl_seconds", 5.0),
                        resume_on_interrupt=event.get("resume_on_interrupt", False),
                    )
                else:
                    player.play(event)
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
            nav_state["last_announced"] = time.time()

    # Hilo que repite el paso actual cada 15s mientras navegación está activa
    def nav_announcer():
        while running:
            if nav_state["active"] and not ptt_active.is_set() and (time.time() - nav_state["last_announced"]) >= 15:
                announce_nav_step()
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
            player.enqueue(audio, priority=1, interrupt=False, ttl_seconds=6.0)

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

        # Esperar a que el audio de respuesta termine antes de reanudar el pipeline
        # player.play() es async en el nuevo AudioPlayer — damos margen al worker
        time.sleep(0.15)
        while player.is_playing():
            time.sleep(0.05)
        ptt_active.clear()
        logger.info("PTT — pipeline reanudado")

    # --- Iniciar subsistemas ---
    camera.start()
    processor.start()

    # --- Hilo de display: ventana con video + subtítulos de Gemini ---
    def _wrap_text(text: str, max_chars: int = 60) -> list[str]:
        """Divide el texto en líneas de máximo max_chars caracteres respetando palabras."""
        words = text.split()
        lines = []
        current = ""
        for word in words:
            if not current:
                current = word
            elif len(current) + 1 + len(word) <= max_chars:
                current += " " + word
            else:
                lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines

    def display_loop():
        global running
        cv2.namedWindow("KODA Demo", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("KODA Demo", 960, 540)

        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.65
        font_thickness = 1
        line_height = 24
        padding = 8

        while running:
            frame_bytes = camera.get_frame()
            if frame_bytes is not None:
                arr = np.frombuffer(frame_bytes, np.uint8)
                img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
                if img is not None:
                    # Dibujar bounding boxes de objetos detectados
                    detections = processor.last_detections
                    try:
                        for det in detections:
                            x1, y1, x2, y2 = det["xyxy"]
                            color = (0, 0, 255) if det["is_close"] else (0, 255, 0)  # BGR: rojo=cercano, verde=lejano
                            thickness = 3 if det["is_close"] else 2
                            cv2.rectangle(img, (x1, y1), (x2, y2), color, thickness)
                            label_text = f"{det['label']} {det['conf']:.0%}"
                            label_y = max(y1 - 6, 12)
                            cv2.putText(img, label_text, (x1, label_y), font, 0.55, color, 1, cv2.LINE_AA)
                    except Exception as e:
                        pass

                    # Contador de detecciones en esquina superior izquierda
                    status_text = f"YOLO: {len(detections)} obj"
                    cv2.putText(img, status_text, (10, 25), font, 0.6, (0, 255, 255), 2, cv2.LINE_AA)

                    description = processor.last_description or ""
                    if description:
                        lines = _wrap_text(description, max_chars=60)
                        overlay_h = line_height * len(lines) + padding * 2
                        h, w = img.shape[:2]
                        overlay_y = h - overlay_h

                        # Rectángulo negro semitransparente como fondo del subtítulo
                        overlay = img.copy()
                        cv2.rectangle(overlay, (0, overlay_y), (w, h), (0, 0, 0), -1)
                        cv2.addWeighted(overlay, 0.55, img, 0.45, 0, img)

                        # Dibujar cada línea de texto en blanco
                        for i, line in enumerate(lines):
                            text_y = overlay_y + padding + line_height * i + line_height - 4
                            cv2.putText(img, line, (padding, text_y), font, font_scale,
                                        (255, 255, 255), font_thickness, cv2.LINE_AA)

                    cv2.imshow("KODA Demo", img)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                logger.info("Usuario cerró la ventana de display — apagando sistema")
                running = False
                break
            time.sleep(1 / 15)

        cv2.destroyAllWindows()

    threading.Thread(target=display_loop, daemon=True).start()
    logger.info("Hilo de display iniciado — ventana 'KODA Demo' activa")

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
        logger.info("Senal de interrupcion recibida - apagando sistema...")
        running = False
        camera.stop()
        stt.stop()
        ptt.stop()
        processor.stop()
        player.shutdown()
        if pygame is not None:
            pygame.quit()

    signal.signal(signal.SIGINT, shutdown_handler)

    # --- Loop principal a ~1 FPS: captura frame → OCR → cola del Processor ---
    prev_frame: bytes | None = None
    _similarity_scores: collections.deque = collections.deque(maxlen=5)
    while running:
        # Pausar captura mientras PTT está activo — no enviar frames ni descripciones
        if ptt_active.is_set():
            time.sleep(0.1)
            continue
        frame = camera.get_frame()
        if frame is not None:
            # Descartar si la escena no cambió — umbral adaptivo: alto cuando quieto, bajo cuando en movimiento
            if prev_frame is not None:
                score = _frame_similarity_score(prev_frame, frame)
                _similarity_scores.append(score)
                avg = sum(_similarity_scores) / len(_similarity_scores)
                threshold = FRAME_SIMILARITY_THRESHOLD_STILL if avg >= FRAME_MOTION_DETECT_THRESHOLD else FRAME_SIMILARITY_THRESHOLD_MOVING
                if score >= threshold:
                    logger.debug(f"Frame descartado — similitud {score:.3f} >= umbral {threshold:.2f} (avg={avg:.3f})")
                    time.sleep(1.0)
                    continue
            prev_frame = frame
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
