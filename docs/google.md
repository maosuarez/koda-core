# Configuración API Google / Koda

Este proyecto utiliza la API de Google Gemini.

## Pasos de configuración:
1. Crear archivo `.env` en la raíz (usar `.env.example` como base).
2. Añadir `GOOGLE_API_KEY=tu_api_key_aqui`.
3. Cargar siempre mediante `python-dotenv`.

## Restricciones:
- No hardcodear API keys.
- Medir y loguear latencia de cada llamada a la API.
