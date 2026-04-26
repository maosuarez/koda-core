# KODA Core

Prototipo técnico de asistencia visual con IA para personas con discapacidad visual severa.
Demo en vivo: 29 de abril de 2026 — Campus Universidad de La Sabana.

## Setup rápido

### 1. Requisitos del sistema
- **Python 3.11+**
- **Tesseract OCR:** Instalado en el sistema (`apt install tesseract-ocr` o similar).

### 2. Configuración
1. Clonar repositorio.
2. `pip install -r requirements.txt`
3. Copiar `.env.example` a `.env` y configurar las claves necesarias.

### 3. Ejecución
```bash
python main.py
```

## Estructura del proyecto
- `main.py`: Orquestador principal.
- `config.py`: Gestión de configuración.
- `camera.py`: Módulo de visión.
- `gemini_client.py`: Cliente de IA.
- `tts_client.py`: Conversión texto-a-voz.
- `stt_client.py`: Conversión voz-a-texto.
- `ocr.py`: Extracción de texto.
- `audio.py`: Reproducción de sonido.
- `prompts.py`: Prompts de IA.
