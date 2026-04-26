# KODA Core

Prototipo técnico de asistencia visual con IA para personas con discapacidad visual severa.
Demo en vivo: 29 de abril de 2026 — Campus Universidad de La Sabana.

## Setup rápido

### 1. Requisitos del sistema
- **Python 3.11+**
- **Tesseract OCR:** Instalado en el sistema con soporte para español.

#### Instalación de Tesseract OCR

**Windows:**
1. Instalar el motor Tesseract:
   ```
   choco install tesseract
   ```
   O descargar manualmente desde: https://github.com/UB-Mannheim/tesseract/wiki

2. Instalar el paquete de idioma español (obligatorio para OCR):
   - Descarga `spa.traineddata` desde: https://github.com/tesseract-ocr/tessdata_best/raw/main/spa.traineddata
   - Copia el archivo a: `C:\Program Files\Tesseract-OCR\tessdata\`
   
   O usa PowerShell:
   ```powershell
   Invoke-WebRequest -Uri "https://github.com/tesseract-ocr/tessdata_best/raw/main/spa.traineddata" -OutFile "C:\Program Files\Tesseract-OCR\tessdata\spa.traineddata"
   ```

**Linux (Ubuntu/Debian):**
```bash
sudo apt install tesseract-ocr tesseract-ocr-spa
```

**macOS:**
```bash
brew install tesseract tesseract-lang
```

**Verificación:**
Ejecuta en terminal/CMD para confirmar que el idioma español está disponible:
```bash
tesseract --list-langs
```
El output debe incluir `spa`.

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
