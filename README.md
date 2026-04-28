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

#### Modelo de detección de objetos: YOLO

- YOLO (YOLOv8n) es el motor de detección visual de objetos del sistema. Es **crítico** para que la ventana de demo muestre los bordes rojo/verde sobre personas, vehículos y obstáculos.
- Se instala automáticamente al hacer `pip install -r requirements.txt` (el paquete `ultralytics` ya está en requirements).
- El modelo `yolov8n.pt` **se descarga automáticamente** la primera vez que se ejecuta `python main.py` (requiere conexión a internet, ~6 MB).
- Para descargarlo manualmente antes de la demo (recomendado si hay conexión limitada):
  ```python
  from ultralytics import YOLO
  YOLO("yolov8n.pt")  # descarga y guarda en el directorio actual
  ```
- Verificación: al arrancar el sistema, los logs deben mostrar:
  ```
  INFO:modules.processing.hazard_detector:Modelo YOLO cargado para deteccion de peligros
  INFO:modules.processing.hazard_detector:YOLO listo — modelo: yolov8n.pt
  ```
- Si aparece `YOLO no disponible`, ejecutar: `pip install ultralytics`

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

### Modo Demo: video pregrabado

- El sistema puede correr con un video MP4 en lugar de cámara en vivo — ideal para demos controladas.
- Para activarlo, agregar esta variable en el archivo `.env`:
  ```
  VIDEO_PATH=demo/mi_video.mp4
  ```
  Acepta rutas relativas al directorio del proyecto o absolutas.
- El video hace loop automático al terminar.
- Para volver a cámara en vivo: comentar o eliminar la línea `VIDEO_PATH` del `.env`.
- Al arrancar en modo demo, los logs confirman:
  ```
  INFO:modules.input.camera:Modo demo: usando video pregrabado 'demo/mi_video.mp4'
  ```

### 3. Ejecución
```bash
python main.py
```

#### Ventana de demo

- Al ejecutar `python main.py`, se abre automáticamente una ventana **"KODA Demo"** que muestra:
  - El video o feed de cámara en tiempo real
  - **Bordes ROJOS** sobre objetos cercanos (peligro inmediato)
  - **Bordes VERDES** sobre objetos detectados a distancia segura
  - Subtítulos con la descripción de Gemini en la parte inferior
  - Contador `YOLO: N obj` en la esquina superior izquierda
- Presionar `q` en la ventana cierra el sistema limpiamente.
- El umbral de proximidad (cuándo un objeto pasa de verde a rojo) se configura en `.env`:
  ```
  HAZARD_PROXIMITY_THRESHOLD=0.05   # 5% del frame = objeto cercano → rojo
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
