# Roadmap del Proyecto Koda - Demo 29 de Abril 2026

## Equipo
- **Nicolás:** Entrada de datos (Vídeos, recopilación de datos).
- **Tomás:** Salida de datos (Abuso, procesamiento de respuesta).
- **IA (Orchestrator):** Delegación, orquestación, revisión técnica.

---

## Plan de Acción (Checklist)

### 1. Configuración y Estructura
- [ ] Verificar y configurar `.env` con las API keys (IA/Tomás)
- [ ] Instalar dependencias necesarias (`requirements.txt`) (IA)
- [ ] Estructura base del proyecto funcional (System Architect)

### 2. Nicolás: Entrada de Datos
- [ ] Configurar acceso a cámara (`camera.py`) (Nicolás/Senior Implementer)
- [ ] Implementar captura y pre-procesamiento de vídeo (Nicolás/Senior Implementer)

### 3. Tomás: Salida de Datos
- [ ] Configurar cliente Gemini API (`gemini_client.py`) con logging de latencia (Tomás/Senior Implementer)
- [ ] Implementar cliente TTS (`tts_client.py`) con logging de latencia (Tomás/Senior Implementer)

### 4. Integración y Optimización (IA)
- [ ] Montar pipeline principal y manejo de hilos (System Architect)
- [ ] Medición y optimización de latencia E2E (Performance Optimizer)
- [ ] Revisión de seguridad y estabilidad final (Adversarial Code Reviewer)

---
*Nota: Todo el trabajo se centra exclusivamente en que la demo funcione el 29 de abril.*
