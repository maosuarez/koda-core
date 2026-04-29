# KODA — Demo en Vivo

## Fecha y lugar

**29 de abril de 2026 — Campus Universidad de La Sabana, Chía, Colombia**

Evaluación ante jurado de hackathon. Sistema desplegado en laptop local con webcam y auriculares de conducción ósea.

---

## Video de demostración

[![KODA Demo Video](https://img.shields.io/badge/VIDEO-PROTOTIPO%202026-red?style=for-the-badge&logo=youtube)](https://www.youtube.com/watch?v=PLACEHOLDER_VIDEO_ID)

*El video se cargará aquí antes de la evaluación. Link temporal a las grabaciones de la demo en vivo.*

---

## Flujo visual de la demo

### 1. Ventana KODA en tiempo real

```
┌─────────────────────────────────────────────────┐
│ KODA Demo                                       │
│                                                 │
│  ┌─────────────────────────────────────────┐   │
│  │                                         │   │
│  │   [VIDEO/CÁMARA EN TIEMPO REAL]        │   │
│  │                                         │   │
│  │   YOLO: 3 objetos detectados           │   │
│  │   - Persona (VERDE, distancia segura)  │   │
│  │   - Escaleras (ROJO, peligro inmediato│   │
│  │   - Puerta (VERDE)                     │   │
│  │                                         │   │
│  └─────────────────────────────────────────┘   │
│                                                 │
│  📝 "Frente a ti hay unas escaleras que bajan │
│  unos 2 metros. A tu derecha, una puerta      │
│  cerrada. Piso de baldosa gris."              │
│                                                 │
└─────────────────────────────────────────────────┘
```

### 2. Elementos visuales clave

| Elemento | Propósito | Color | Comportamiento |
|----------|-----------|-------|----------------|
| **Bordes de objetos** | Detección YOLO | ROJO (peligro) / VERDE (seguro) | Se actualizan en tiempo real cada 1 FPS |
| **Contador YOLO** | Confirmación de detección | Blanco sobre fondo oscuro | Esquina superior izquierda; muestra cantidad de objetos |
| **Subtítulos de Gemini** | Descripción de escena | Blanco, centrado | Parte inferior de la ventana; se reemplaza cada 2-3 seg |
| **Indicador de escucha** | Estado de STT | Azul intermitente | Parpadea cuando el usuario presiona PTT |

---

## Flujo de la demo en 3 actos

### Acto 1: Descripción automática (30 segundos)

El sistema arranca y comienza a describir automáticamente lo que ve:

1. Cámara captura video en vivo
2. Detector YOLO identifica objetos → bordes rojo/verde en la pantalla
3. Tesseract OCR extrae texto visible
4. Gemini describe la escena en 1-2 oraciones
5. TTS sintetiza en español
6. Usuario escucha a través de auriculares/altavoz

**Métricas observables:**
- Latencia E2E: < 1.5 segundos (desde captura hasta audio)
- Descripción clara de peligros inmediatos y contexto general
- Contador YOLO muestra detecciones en tiempo real

### Acto 2: Pregunta por voz (30 segundos)

El usuario presiona botón PTT (o tecla) y hace una pregunta:

**Usuario dice:** "¿Qué está frente a mí?"

1. STT captura audio del micrófono
2. Transforma a texto: "¿Qué está frente a mí?"
3. Sistema detecta como pregunta (no navegación)
4. Gemini responde con contexto visual actual
5. TTS sintetiza respuesta
6. Usuario escucha

**Métricas observables:**
- STT funciona correctamente
- Respuesta es contextual a la escena visible
- Latencia < 2 segundos

### Acto 3: Navegación paso a paso (45 segundos)

El usuario prueba el sistema de navegación mock:

**Usuario dice:** "¿Cómo llego al bloque G?"

1. Sistema detecta palabra clave "bloque" → identificanavegación
2. Busca en landmarks del campus mock
3. Responde: "El Bloque G está a 3 minutos caminando..."
4. Usuario dice: "Navega paso a paso"
5. Sistema inicia navegación continua
6. Anuncia pasos: "Paso 1: Sal por la puerta principal..."
7. Usuario dice: "Siguiente"
8. Sistema avanza a siguiente paso

**Métricas observables:**
- Detección de intents funciona
- Navegación paso a paso es coherente
- Sin dependencia de Google Maps (modo mock)
- Demo puede ocurrir offline

---

## Casos de uso demostrados

### 1. Descripción de escena

**Qué ve el jurado:**
- Ventana con video en tiempo real
- Bordes rojo/verde sobre objetos
- Subtítulos que describen lo que Gemini "ve"
- Sistema automáticamente actualiza descripción cada 2-3 segundos

**Éxito si:**
- Detección de peligros correcta (escaleras, obstáculos → ROJO)
- Descripción coherente con la escena visible
- Latencia aceptable (sin lag notable)

### 2. Pregunta por voz

**Qué ve el jurado:**
- Usuario presiona botón PTT
- Sistema muestra indicador de escucha (interfaz visual mínima)
- Audio sintetizado responde a la pregunta

**Éxito si:**
- STT captura correctamente la pregunta
- Respuesta de Gemini es inteligente y contextual
- TTS es claro y en español natural

### 3. Navegación en campus

**Qué ve el jurado:**
- Usuario dice "¿Cómo llego al bloque G?"
- Sistema responde con instrucciones de navegación
- Navegación paso a paso funciona sin Maps API
- Usuario puede cancelar en cualquier momento

**Éxito si:**
- Palabras clave se detectan correctamente
- Respuestas del mock son coherentes
- Sistema no se cae si Maps no está disponible

---

## Métricas técnicas

### Latencia esperada

```
Captura frame:              ~30 ms
├─ OCR (Tesseract):        ~100-200 ms (paralelo)
├─ Envío a Gemini:         ~100 ms
├─ Procesamiento Gemini:   ~300-800 ms  ← cuello de botella
└─ Red (return):           ~100 ms

Síntesis TTS:              ~50-200 ms
├─ Reproducción audio:     ~100 ms

TOTAL E2E OBJETIVO:        < 1.5 segundos
```

### Distribución de tiempo (caso típico)

| Componente | Min | Típico | Max | % del total |
|-----------|-----|--------|-----|-------------|
| **Captura + preproc** | 30 ms | 50 ms | 100 ms | 3-6% |
| **OCR** | 80 ms | 150 ms | 300 ms | 10-20% |
| **Red Gemini** | 100 ms | 150 ms | 300 ms | 10-20% |
| **Gemini inference** | 300 ms | 500 ms | 800 ms | 33-53% |
| **TTS** | 50 ms | 100 ms | 200 ms | 6-13% |
| **Audio playback** | 80 ms | 100 ms | 150 ms | 5-10% |
| **Overhead sistema** | 50 ms | 100 ms | 150 ms | 6-10% |
| **TOTAL** | 690 ms | 1150 ms | 2000 ms | 100% |

### Configuración de hardware

- **CPU:** Intel Core i7/i9 (2021+) — recomendado para procesamiento Gemini en tiempo real
- **RAM:** 8 GB mínimo (típicamente se usan 2-3 GB en demo)
- **Cámara:** Webcam 1080p @ 30 FPS (se capturan 1 FPS enviados a Gemini)
- **Micrófono:** Estándar USB (mínimo SNR 80 dB)
- **Auriculares:** De conducción ósea o estándar (compatible con pygame/playsound)
- **Red:** Conexión estable a internet (> 2 Mbps recomendado)

---

## Checklist pre-demo

### Configuración del sistema (día antes)

- [ ] `.env` configurado con `GEMINI_API_KEY` válida
- [ ] `.env` configurado con `GOOGLE_CLOUD_PROJECT` y credenciales TTS/STT
- [ ] `python -m pip install -r requirements.txt` ejecutado
- [ ] Tesseract OCR instalado y verificado (`tesseract --list-langs` incluye `spa`)
- [ ] YOLO modelo `yolov8n.pt` descargado (auto-descarga primera vez, ~6 MB)
- [ ] Micrófono y altavoz/auriculares testeados
- [ ] Video de demo pregrabado en `demo/video_demo.mp4` (opcional, ideal para demo reproducible)

### Día de la demo

- [ ] Arrancar `python main.py` — verifica que ventana KODA abre sin errores
- [ ] Cámara captura frames correctamente (video visible en ventana)
- [ ] YOLO detecta objetos (contador "YOLO: N obj" visible)
- [ ] Subtítulos aparecen en la ventana (Gemini está funcionando)
- [ ] Audio se escucha en altavoz/auriculares (TTS está funcionando)
- [ ] Presionar PTT y hacer pregunta — responde correctamente
- [ ] Decir "¿Cómo llego al bloque G?" — detecta navegación y responde
- [ ] Latencia E2E medida y documentada (< 1.5 seg es objetivo)
- [ ] Conexión a internet estable (Google APIs requieren conexión)

---

## Modos de ejecución

### Modo 1: Cámara en vivo (por defecto)

```bash
python main.py
```

- Captura desde webcam conectada
- Sistema describe continuamente lo que ve
- Ideal para demostración en tiempo real

### Modo 2: Video pregrabado (demo reproducible)

```bash
# En .env:
VIDEO_PATH=demo/video_demo.mp4
python main.py
```

- Usa video MP4 en lugar de cámara
- Video hace loop al terminar
- Permite demo consistente y predecible
- Ideal si hay problemas de iluminación o latencia de cámara

---

## Posibles problemas y soluciones

| Problema | Causa | Solución |
|----------|-------|----------|
| "YOLO no disponible" | `ultralytics` no instalado | `pip install ultralytics` |
| Bordes rojo/verde no aparecen | Modelo YOLO no descargado | Esperar 30 seg en primer arranque, o `python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"` |
| "Tesseract no encontrado" | No instalado o PATH incorrecto | `brew install tesseract` (macOS) o descarga ejecutable (Windows) |
| Sin audio | Pygame no instalado o micrófono sin sonido | `pip install pygame`, revisar volumen del sistema |
| Gemini lento / timeout | Red inestable o API quota alcanzada | Reintentar, o usar video pregrabado sin red (limitado) |
| STT no funciona | Google Cloud credentials incompletos | Verificar `GOOGLE_APPLICATION_CREDENTIALS` en `.env` |

---

## Referencias rápidas

- **README.md** — Setup y configuración completa
- **context.md** — Contexto arquitectónico interno
- **mock.md** — Documentación del sistema de navegación sin Maps API
- **tests/README.md** — Cómo ejecutar pruebas unitarias
- **modules/prompts.py** — Prompts de Gemini (iterables por Mao)

---

## Resumen para el jurado

KODA es un sistema de **asistencia visual en tiempo real con IA** para personas con discapacidad visual severa. La demo del 29 de abril muestra:

1. **Visión automática:** Sistema describe continuamente la escena usando YOLO + Gemini 2.5 Flash
2. **Detección de peligros:** Bordes rojo/verde identifican obstáculos inmediatos vs. distancia segura
3. **Conversación por voz:** Usuario pregunta "¿Qué es esto?" y recibe respuesta contextual
4. **Navegación sin GPS:** Usuario puede pedir dirección a destinos del campus sin Google Maps
5. **Latencia real:** Descripción completa en < 1.5 segundos

**Tecnologías:** Python 3.11 + Google Gemini 2.5 Flash + Google Cloud TTS/STT + OpenCV + YOLOv8n + Tesseract OCR.

El sistema corre **100% local sin backend**, demostrando independencia operacional en un ambiente universitario real.
