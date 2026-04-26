import json
import os
import queue
import threading
import time
import logging
from typing import Callable

import pyaudio
from google.cloud import speech_v2
from google.cloud.speech_v2.types import cloud_speech
from modules import config

logger = logging.getLogger(__name__)

# Parámetros de captura de micrófono
_RATE = 16000
_CHUNK = 1024
_CHANNELS = 1
_FORMAT = pyaudio.paInt16
_MAX_RETRIES = 3


class SpeechToTextClient:
    def __init__(self):
        self._running = False
        self._thread = None
        self._audio_queue: queue.Queue = queue.Queue()
        self._pa: pyaudio.PyAudio | None = None
        self._mic_stream = None
        self._callback: Callable[[str], None] | None = None

        # Validar credenciales antes de intentar conectar
        creds_path = config.GOOGLE_APPLICATION_CREDENTIALS
        if not creds_path or not os.path.exists(creds_path):
            raise RuntimeError(f"GOOGLE_APPLICATION_CREDENTIALS inválido o inexistente: {creds_path}")

        # Leer project_id desde el JSON de credenciales para construir el recognizer path
        with open(creds_path) as f:
            project_id = json.load(f)["project_id"]
        self._recognizer = f"projects/{project_id}/locations/global/recognizers/_"
        logger.info(f"STT inicializado — proyecto: {project_id}")

    def start(self, callback: Callable[[str], None]) -> None:
        self._callback = callback
        self._running = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()
        logger.info("Escucha STT iniciada en hilo separado")

    def stop(self) -> None:
        self._running = False
        self._close_mic()
        if self._thread:
            self._thread.join(timeout=3)
        logger.info("Cliente STT detenido")

    def _listen_loop(self) -> None:
        attempts = 0
        while self._running and attempts < _MAX_RETRIES:
            try:
                self._stream_once()
                # Si terminó limpiamente sin excepción, reiniciar contador
                attempts = 0
            except Exception as e:
                attempts += 1
                logger.warning(f"Stream STT interrumpido (intento {attempts}/{_MAX_RETRIES}): {e}")
                self._close_mic()
                if attempts >= _MAX_RETRIES:
                    logger.error("Máximo de reconexiones STT alcanzado — deteniendo escucha")
                    break
                time.sleep(1)

    def _stream_once(self) -> None:
        # Vaciar cola de audio de sesiones anteriores
        while not self._audio_queue.empty():
            self._audio_queue.get_nowait()

        self._pa = pyaudio.PyAudio()
        self._mic_stream = self._pa.open(
            format=_FORMAT,
            channels=_CHANNELS,
            rate=_RATE,
            input=True,
            frames_per_buffer=_CHUNK,
            stream_callback=self._audio_callback,
        )
        self._mic_stream.start_stream()

        client = speech_v2.SpeechClient()
        streaming_config = self._build_streaming_config()
        logger.info("Stream de reconocimiento iniciado")

        # Marca de tiempo para medir latencia por utterance
        utterance_start = time.time()

        responses = client.streaming_recognize(
            requests=self._request_generator(streaming_config)
        )

        for response in responses:
            if not self._running:
                break
            for result in response.results:
                if result.is_final:
                    transcript = result.alternatives[0].transcript.strip()
                    latency_ms = (time.time() - utterance_start) * 1000
                    logger.info(f"Utterance detectado ({latency_ms:.1f}ms): '{transcript}'")
                    if transcript and self._callback:
                        self._callback(transcript)
                    utterance_start = time.time()

        self._close_mic()

    def _audio_callback(self, in_data, frame_count, time_info, status) -> tuple:
        self._audio_queue.put(in_data)
        return None, pyaudio.paContinue

    def _request_generator(self, streaming_config: cloud_speech.StreamingRecognitionConfig):
        # Primer request: solo configuración, sin audio
        yield cloud_speech.StreamingRecognizeRequest(
            recognizer=self._recognizer,
            streaming_config=streaming_config,
        )
        # Requests siguientes: chunks de audio del micrófono
        while self._running:
            try:
                chunk = self._audio_queue.get(timeout=1)
                yield cloud_speech.StreamingRecognizeRequest(audio=chunk)
            except queue.Empty:
                continue

    def _build_streaming_config(self) -> cloud_speech.StreamingRecognitionConfig:
        recognition_config = cloud_speech.RecognitionConfig(
            explicit_decoding_config=cloud_speech.ExplicitDecodingConfig(
                encoding=cloud_speech.ExplicitDecodingConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=_RATE,
                audio_channel_count=_CHANNELS,
            ),
            language_codes=["es-CO", "es-US"],
            model="latest_long",
        )
        return cloud_speech.StreamingRecognitionConfig(
            config=recognition_config,
            streaming_features=cloud_speech.StreamingRecognitionFeatures(
                interim_results=False,
            ),
        )

    def _close_mic(self) -> None:
        if self._mic_stream:
            try:
                self._mic_stream.stop_stream()
                self._mic_stream.close()
            except Exception:
                pass
            self._mic_stream = None
        if self._pa:
            try:
                self._pa.terminate()
            except Exception:
                pass
            self._pa = None
