import io
import json
import os
import queue
import threading
import time
import logging
import winsound
from typing import Callable

import pyaudio
import keyboard
from google.cloud import speech_v2
from google.cloud.speech_v2.types import cloud_speech
from modules import config
from modules.output.audio import AudioPlayer

logger = logging.getLogger(__name__)

_RATE = 16000
_CHUNK = 1024
_CHANNELS = 1
_FORMAT = pyaudio.paInt16

# Intervalo del loop de polling de teclado — 20ms es suficiente para no perder el flanco de soltar Enter
_POLL_INTERVAL = 0.02


class PushToTalkClient:
    def __init__(
        self,
        ptt_active: threading.Event,
        player: AudioPlayer,
        processor_output_queue: queue.Queue,
    ):
        self._ptt_active = ptt_active
        self._player = player
        self._processor_output_queue = processor_output_queue

        self._running = False
        self._thread: threading.Thread | None = None
        self._callback: Callable[[str], None] | None = None

        creds_path = config.GOOGLE_APPLICATION_CREDENTIALS
        if not creds_path or not os.path.exists(creds_path):
            raise RuntimeError(f"GOOGLE_APPLICATION_CREDENTIALS inválido o inexistente: {creds_path}")

        with open(creds_path) as f:
            project_id = json.load(f)["project_id"]
        self._recognizer = f"projects/{project_id}/locations/global/recognizers/_"
        logger.info(f"PushToTalk inicializado — proyecto: {project_id}")

    def start(self, callback: Callable[[str], None]) -> None:
        self._callback = callback
        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=3)
        logger.info("PushToTalk detenido")

    def _poll_loop(self) -> None:
        was_pressed = False
        frames: list[bytes] = []
        pa: pyaudio.PyAudio | None = None
        stream = None

        while self._running:
            is_pressed = keyboard.is_pressed("enter")

            if is_pressed and not was_pressed:
                # Flanco de bajada: pausar pipeline, interrumpir audio, pitido, empezar a grabar
                self._ptt_active.set()
                self._player.stop_current()
                self._player.clear_queue()   # drenar cola interna del player

                # Limpiar cola de audio pendiente para no reproducir descripciones viejas post-PTT
                while not self._processor_output_queue.empty():
                    try:
                        self._processor_output_queue.get_nowait()
                    except queue.Empty:
                        break

                # Pitido de "ahora escucho" — bloqueante, 880 Hz, 200 ms
                winsound.Beep(880, 200)

                frames = []
                try:
                    pa = pyaudio.PyAudio()
                    stream = pa.open(
                        format=_FORMAT,
                        channels=_CHANNELS,
                        rate=_RATE,
                        input=True,
                        frames_per_buffer=_CHUNK,
                    )
                    stream.start_stream()
                    logger.info("PTT — grabando...")
                except Exception as e:
                    logger.error(f"PTT — no se pudo abrir el micrófono: {e}")
                    pa = None
                    stream = None

            elif is_pressed and was_pressed:
                # Tecla sostenida: leer chunk disponible
                if stream is not None:
                    try:
                        data = stream.read(_CHUNK, exception_on_overflow=False)
                        frames.append(data)
                    except Exception as e:
                        logger.warning(f"PTT — error leyendo audio: {e}")

            elif not is_pressed and was_pressed:
                # Flanco de subida: detener grabación y transcribir
                if stream is not None:
                    try:
                        stream.stop_stream()
                        stream.close()
                    except Exception:
                        pass
                    stream = None
                if pa is not None:
                    try:
                        pa.terminate()
                    except Exception:
                        pass
                    pa = None

                if frames:
                    audio_bytes = b"".join(frames)
                    logger.info(f"PTT — grabación terminada ({len(audio_bytes) / _RATE / 2:.2f}s), transcribiendo...")
                    # _transcribe llama al callback; el callback limpia ptt_active al terminar
                    self._transcribe(audio_bytes)
                else:
                    # Sin audio grabado — reanudar pipeline de inmediato
                    self._ptt_active.clear()
                    logger.info("PTT — sin audio grabado, pipeline reanudado")
                frames = []

            was_pressed = is_pressed
            time.sleep(_POLL_INTERVAL)

        # Cleanup si el loop termina mientras se graba
        if stream is not None:
            try:
                stream.stop_stream()
                stream.close()
            except Exception:
                pass
        if pa is not None:
            try:
                pa.terminate()
            except Exception:
                pass

    def _transcribe(self, audio_bytes: bytes) -> None:
        t0 = time.time()
        try:
            client = speech_v2.SpeechClient()
            config_obj = cloud_speech.RecognitionConfig(
                explicit_decoding_config=cloud_speech.ExplicitDecodingConfig(
                    encoding=cloud_speech.ExplicitDecodingConfig.AudioEncoding.LINEAR16,
                    sample_rate_hertz=_RATE,
                    audio_channel_count=_CHANNELS,
                ),
                language_codes=["es-CO", "es-US"],
                # "latest_short" es más preciso para utterances cortos (< 60s)
                model="latest_short",
            )
            request = cloud_speech.RecognizeRequest(
                recognizer=self._recognizer,
                config=config_obj,
                content=audio_bytes,
            )
            response = client.recognize(request=request)
            latency_ms = (time.time() - t0) * 1000

            if response.results:
                transcript = response.results[0].alternatives[0].transcript.strip()
                logger.info(f"PTT — transcripción ({latency_ms:.1f}ms): '{transcript}'")
                if transcript and self._callback:
                    self._callback(transcript)
                else:
                    # Transcript vacío — reanudar pipeline
                    self._ptt_active.clear()
                    logger.info("PTT — transcript vacío, pipeline reanudado")
            else:
                # Sin resultado (silencio) — reanudar pipeline
                self._ptt_active.clear()
                logger.info(f"PTT — sin resultado ({latency_ms:.1f}ms) — posiblemente silencio, pipeline reanudado")
        except Exception as e:
            # Error en STT — reanudar pipeline para no dejarlo bloqueado indefinidamente
            self._ptt_active.clear()
            logger.error(f"PTT — transcripción falló: {e} — pipeline reanudado")
