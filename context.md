# KODA Core — Prototipo técnico de asistencia visual con IA

## Descripción

KODA es un sistema de asistencia visual en tiempo real para personas con discapacidad visual severa.
Captura video desde una cámara (webcam o teléfono), lo envía a Gemini 2.5 Flash para análisis multimodal,
y devuelve descripciones de escena habladas en español colombiano a través de auriculares de conducción ósea.
El usuario también puede hacer preguntas por voz que el sistema interpreta y responde con navegación contextual.

Este repositorio contiene el **núcleo técnico del prototipo** para demostración en hackathon (29 abril 2026).
No es producción. Es la fachada funcional mínima que hace el flujo completo: ver → entender → hablar.

---

## Stack

- **Lenguaje:** Python 3.11+
- **IA principal:** Google Gemini 2.5 Flash API (`google-generativeai`)
- **Voz saliente:** Google Cloud Text-to-Speech Neural2 (`google-cloud-texttospeech`) — voz `es-US-Neural2-B` o `es-CO` si disponible
- **Voz entrante (STT):** Google Cloud Speech-to-Text v2 (`google-cloud-speech`) — streaming con micrófono
- **Captura de cámara:** OpenCV (`cv2`) — webcam local o cámara IP
- **OCR en escena:** Tesseract vía `pytesseract` + preprocesamiento con OpenCV (extracción de texto visible en la imagen)
- **Audio playback:** `pygame.mixer` o `playsound` para reproducir el TTS
- **Micrófono:** `pyaudio` para captura de audio en streaming
- **Navegación (opcional para demo):** Google Maps Platform — Directions API o Places API vía `googlemaps`
- **Variables de entorno:** `python-dotenv` para gestión de API keys

---

## Arquitectura

```
Cámara (OpenCV)
    │
    ▼
Frame captura (1 FPS por defecto, ajustable)
    │
    ├──► OCR pipeline (Tesseract)
    │         └── Texto detectado en escena → se incluye en el prompt a Gemini
    │
    ▼
Gemini 2.5 Flash API
    │   Prompt: descripción de escena + priorización (obstáculos urgentes primero)
    │   Input: imagen base64 + texto OCR + historial de conversación
    │
    ▼
Respuesta de texto (descripción o respuesta a pregunta)
    │
    ▼
Google Cloud TTS Neural2 (español)
    │
    ▼
Audio → auricular de conducción ósea (o altavoz/audífonos en demo)
    │
    ▲
    │
Micrófono (PyAudio + Google STT)
    └── Comando de voz del usuario → se añade al contexto de la conversación
```

**Dos modos de operación:**

1. **Modo descripción continua** — cada N segundos, captura frame y describe la escena automáticamente
2. **Modo conversacional** — el usuario activa con voz, hace una pregunta, el sistema responde con contexto visual actual

Los dos modos pueden correr en paralelo con hilos (`threading`).

---

## Convenciones

- Idioma de código: inglés (variables, funciones, clases)
- Idioma de comentarios: español
- Idioma de todos los outputs de voz: español colombiano
- Naming: `snake_case` para funciones y variables, `PascalCase` para clases
- Un archivo por módulo: `camera.py`, `gemini_client.py`, `tts_client.py`, `stt_client.py`, `ocr.py`, `audio.py`, `main.py`
- Configuración centralizada en `config.py` o `.env` — nunca hardcodear API keys
- Logs con `logging` estándar de Python, nivel INFO por defecto

---

## Estructura de archivos objetivo

```
koda-core/
├── main.py               # Punto de entrada — orquesta los módulos
├── config.py             # Configuración y carga de variables de entorno
├── camera.py             # Captura de frames con OpenCV
├── gemini_client.py      # Cliente Gemini 2.5 Flash — envío de imagen + prompt
├── tts_client.py         # Google Cloud TTS Neural2 — texto a audio
├── stt_client.py         # Google Cloud STT — audio a texto (streaming)
├── ocr.py                # Extracción de texto visible en la imagen (Tesseract)
├── audio.py              # Reproducción de audio (pygame o playsound)
├── prompts.py            # Prompts de Gemini centralizados (NO hardcodeados en gemini_client.py)
├── .env                  # API keys (no commitear)
├── .env.example          # Template de variables requeridas
├── requirements.txt      # Dependencias
└── README.md             # Instrucciones de setup y ejecución
```

---

## Prompts de Gemini — Diseño clave

Los prompts viven en `prompts.py`. Hay dos:

**`SCENE_DESCRIPTION_PROMPT`** — para descripción continua:
```
Eres el guía visual de una persona ciega. Describe la escena en 1-2 oraciones máximo.
Prioridad estricta: primero obstáculos o peligros inmediatos (escalones, objetos en el camino,
personas muy cerca), luego texto visible relevante, luego contexto general.
Si no hay nada urgente, describe brevemente qué tipo de espacio es y qué hay.
Responde SOLO en español. Sé conciso y directo. No uses frases como "en la imagen veo".
Texto detectado por OCR en la escena: {ocr_text}
```

**`CONVERSATION_PROMPT`** — para preguntas del usuario:
```
Eres el guía visual de una persona ciega. Tienes acceso a lo que la cámara está viendo ahora mismo.
El usuario acaba de preguntar: "{user_question}"
Contexto visual actual: {scene_description}
Texto visible en la escena: {ocr_text}
Responde en español colombiano, de forma clara y útil. Si la pregunta es de navegación,
da instrucciones paso a paso ancladas a lo que ves. Máximo 3 oraciones.
```

Los prompts son la variable más crítica del sistema — iterar sobre ellos es parte del trabajo.

---

## Restricciones técnicas

- **No usar Flutter ni Dart** en este prototipo — es Python puro para velocidad de desarrollo
- **No implementar Firebase** — sin backend para el hackathon
- **No implementar modo offline con MediaPipe** — eso es post-hackathon
- **Latencia E2E objetivo:** < 1.5 segundos desde captura hasta que el usuario escucha la descripción
  - Captura frame: ~30ms
  - Red + Gemini: 300–800ms (el cuello de botella)
  - TTS: 50–200ms
  - Reproducción: ~100ms
- **Medir la latencia real** en cada prueba y documentarla — es dato del pitch
- **No enviar frames a Gemini más rápido de lo que el sistema puede procesar** — usar una cola o flag de "en proceso"
- **API keys nunca en el código** — siempre desde `.env` con `python-dotenv`
- **Tesseract debe estar instalado en el sistema** — no solo como librería Python (`brew install tesseract` / `apt install tesseract-ocr`)
- **Lenguaje Tesseract:** configurar con `lang='spa'` para español

---

## Variables de entorno requeridas (`.env.example`)

```
GEMINI_API_KEY=
GOOGLE_CLOUD_PROJECT=
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
GOOGLE_MAPS_API_KEY=          # opcional para demo de navegación
CAMERA_INDEX=0                # índice de la webcam (0 por defecto)
FRAME_RATE=1                  # frames por segundo enviados a Gemini
TTS_LANGUAGE_CODE=es-US       # o es-CO si disponible
TTS_VOICE_NAME=es-US-Neural2-B
```

---

## Contexto de negocio

- **Usuario final:** Sebastián — 23 años, estudiante ciego en campus universitario
- **Caso de uso principal del hackathon:** Usuario se pone las gafas, pregunta "¿cómo llego al bloque G?" y llega solo
- **Demo del 29 de abril:** en el campus de la Universidad de La Sabana, con el jurado presente
- **El jurado evalúa:** que funciona (no que es perfecto) — la demo en vivo vale más que cualquier diapositiva
- **Métricas que hay que poder mostrar:** latencia medida, porcentaje de acierto en descripción de obstáculos

---

## Decisiones ya tomadas — no renegociar

- Stack 100% Google APIs: Gemini + Cloud TTS + Cloud STT (+ Maps opcional)
- Python como lenguaje del prototipo
- OCR incluido en el pipeline de Gemini — el texto detectado se pasa como contexto adicional
- Arquitectura de dos hilos: descripción continua + modo conversacional en paralelo
- La voz de salida es Neural2 en español — no gTTS ni alternativas gratuitas
