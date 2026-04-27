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
4. (Opcional) Configurar parametros de peligro/audio en `.env`:
   - `HAZARD_DETECTION_ENABLED=true`
   - `HAZARD_MODEL_NAME=yolov8n.pt`
   - `HAZARD_COOLDOWN_SECONDS=6`
   - `AUDIO_INTERRUPTIONS_ENABLED=true`
   - `AUDIO_QUEUE_MAXSIZE=12`
   - `AUDIO_DROP_EXPIRED=true`

### 3. Ejecución
```bash
python main.py
```

## Estructura del proyecto
- `main.py`: Orquestador principal.
- `modules/input/`: Captura de camara, OCR y STT.
- `modules/processing/pipeline.py`: Pipeline principal de procesamiento.
- `modules/processing/hazard_rules.py`: Reglas de criticidad para OCR/objetos.
- `modules/processing/hazard_detector.py`: Detector de peligro con YOLO (opcional) + cooldown.
- `modules/output/gemini_client.py`: Cliente de IA para descripcion y conversacion.
- `modules/output/tts_client.py`: Conversion texto-a-voz.
- `modules/output/audio.py`: Cola de audio priorizada, interrupcion y reanudacion.
- `modules/prompts.py`: Prompts de IA.
- `tests/`: Pruebas unitarias y guia de ejecucion (`tests/README.md`).
