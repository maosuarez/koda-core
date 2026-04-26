# Guía de Desarrollo para el equipo Koda

Esta guía define cómo debemos trabajar para llegar a la demo del 29 de abril.

## Roles
- **Nicolás:** Entrada de datos (Cámara, pre-procesamiento).
- **Thomas:** Salida de datos (IA, Procesamiento, TTS).
- **IA (Orchestrator):** Delegación técnica.

## Estructura de trabajo
Hemos organizado el proyecto para mayor claridad:
- `/modules/`: Lógica de negocio (clientes, sensores, configuración).
- `/main.py`: Orquestador principal.

## Instrucciones para Nicolás (Entrada)
1. Enfócate en los archivos dentro de `modules/`: `camera.py`, `ocr.py`.
2. Tu objetivo: asegurar que los frames y el texto detectado lleguen al pipeline principal.
3. Comunícate conmigo para integrar tus módulos con `main.py`.

## Instrucciones para Thomas (Salida)
1. Enfócate en los archivos dentro de `modules/`: `gemini_client.py`, `tts_client.py`, `stt_client.py`, `audio.py`.
2. Tu objetivo: gestionar el procesamiento de la IA y la respuesta de voz.
3. Asegura el logging de latencia.

---
*Recuerda: Solo Python, respetar `.env`, y enfoque absoluto en la demo.*
