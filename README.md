# KODA Core

Prototipo técnico de asistencia visual con IA para personas con discapacidad visual severa.
Demo en vivo: 29 de abril de 2026 — Campus Universidad de La Sabana.

---

## Setup rápido

### 1. Requisitos del sistema

**Python 3.11+**

**Tesseract OCR** (debe instalarse en el sistema, no solo con pip):
```bash
# macOS
brew install tesseract tesseract-lang

# Ubuntu / Debian
sudo apt install tesseract-ocr tesseract-ocr-spa
```

### 2. Clonar e instalar dependencias

```bash
git clone <repo-url>
cd koda-core
pip install -r requirements.txt
```

### 3. Configurar credenciales

```bash
cp .env.example .env
# Editar .env con las API keys reales
```

Credenciales necesarias:
- `GEMINI_API_KEY` — desde [Google AI Studio](https://aistudio.google.com)
- `GOOGLE_APPLICATION_CREDENTIALS` — service account JSON con permisos para Cloud TTS y Cloud STT
- `GOOGLE_CLOUD_PROJECT` — ID del proyecto en Google Cloud

### 4. Correr el sistema

```bash
python main.py
```

---

## Arquitectura del flujo

```
Cámara (OpenCV) → Frame captura (1 FPS)
    ├── OCR (Tesseract) → texto visible en escena
    └── Gemini 2.5 Flash API → descripción priorizada
                                    └── TTS Neural2 → audio en español
                                    
Micrófono (PyAudio) → STT → pregunta del usuario
    └── Gemini 2.5 Flash (con contexto visual) → respuesta
                                    └── TTS Neural2 → audio en español
```

---

## Módulos

| Archivo | Responsabilidad |
|---|---|
| `main.py` | Punto de entrada — orquesta los módulos y los hilos |
| `config.py` | Carga de `.env` y configuración global |
| `camera.py` | Captura de frames con OpenCV |
| `gemini_client.py` | Cliente Gemini 2.5 Flash — imagen + prompt → texto |
| `tts_client.py` | Google Cloud TTS Neural2 — texto → audio |
| `stt_client.py` | Google Cloud STT — audio de micrófono → texto |
| `ocr.py` | Extracción de texto visible en imagen con Tesseract |
| `audio.py` | Reproducción de audio (pygame) |
| `prompts.py` | Prompts de Gemini — NO editar sin coordinar con Mao |

---

## Latencia objetivo

| Etapa | Target |
|---|---|
| Captura de frame | ~30ms |
| Red + Gemini | 300–800ms |
| TTS síntesis | 50–200ms |
| Reproducción | ~100ms |
| **Total E2E** | **< 1.5 seg** |

Medir y loguear la latencia real en cada llamada. Es dato del pitch del hackathon.

---

## Notas para la demo

- La demo principal es: usuario pregunta "¿cómo llego al bloque G?" y el sistema responde con navegación
- El audio de salida va a auriculares de conducción ósea — probar que el nivel de volumen sea adecuado en exteriores
- Si hay problemas de conectividad en el campus, tener un hotspot de respaldo
- Registrar la latencia promedio medida en las pruebas previas para mostrar en el pitch

---

## Contacto del equipo

- **Nicolás Clavijo** — implementación técnica
- **Thomas Gómez** — implementación técnica
- **Mao Suárez** — prompts de Gemini y coordinación
