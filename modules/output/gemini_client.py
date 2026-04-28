import os
import time
import threading
import logging
import cv2
import numpy as np
from google import genai
from google.genai import types
from modules.config import GEMINI_API_KEY, GEMINI_MODEL, USE_VERTEX, GCP_PROJECT, GCP_LOCATION
from modules.prompts import SCENE_DESCRIPTION_PROMPT, CONVERSATION_PROMPT

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if USE_VERTEX.lower() == "true":
    client = genai.Client(
        vertexai=True,
        project=GCP_PROJECT,
        location=GCP_LOCATION,
    )
    logger.info("Gemini via Vertex AI")
else:
    client = genai.Client(api_key=GEMINI_API_KEY)
    logger.info("Gemini via API Key")
_chat = None  # sesión persistente para modo conversacional
_chat_lock = threading.Lock()  # evitar condiciones de carrera en la sesión de chat


def get_scene_description(image_frame: bytes, ocr_text: str = "", recent_history: list[str] | None = None) -> str:
    start_time = time.time()
    try:
        # Re-encodar a JPEG calidad 75 para reducir payload hacia Gemini
        nparr = np.frombuffer(image_frame, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is not None:
            _, buffer = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 75])
            image_frame = buffer.tobytes()

        if recent_history:
            history_text = "\n".join(f"- {h}" for h in recent_history[-3:])
        else:
            history_text = "(sin descripciones previas)"
        prompt = SCENE_DESCRIPTION_PROMPT.format(ocr_text=ocr_text, recent_history=history_text)
        image_part = types.Part.from_bytes(data=image_frame, mime_type="image/jpeg")
        # Sin _chat_lock aquí: generate_content es stateless y no usa _chat
        # El lock solo protege la sesión persistente _chat usada por get_conversation_response
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[image_part, prompt],
        )
        elapsed = time.time() - start_time
        logger.info(f"Latencia Gemini: {elapsed:.4f} segundos")
        return response.text or ""
    except Exception as e:
        logger.error(f"Error en Gemini: {e}")
        return ""


def get_conversation_response(user_question: str, scene_description: str, ocr_text: str = "") -> str:
    global _chat
    start_time = time.time()
    try:
        prompt = CONVERSATION_PROMPT.format(
            user_question=user_question,
            scene_description=scene_description,
            ocr_text=ocr_text,
        )
        with _chat_lock:
            if _chat is None:
                _chat = client.chats.create(model=GEMINI_MODEL)
            response = _chat.send_message(prompt)
        elapsed = time.time() - start_time
        logger.info(f"Latencia Gemini conversación: {elapsed:.4f} segundos")
        return response.text or ""
    except Exception as e:
        logger.error(f"Error en Gemini conversación: {e}")
        return ""


def reset_conversation() -> None:
    global _chat
    with _chat_lock:
        _chat = None
