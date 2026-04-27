# Historial de Cambios para la Implementacion de Prioridades y Peligro

Fecha: 2026-04-26

## Objetivo general
El objetivo principal de esta actualización es dar soporte al sistema subyacente (gafas inteligentes para personas con discapacidad visual). Se pasó de un flujo lineal (donde el asistente describe la escena sin parar) a un sistema inteligente que puede **interrumpir** la descripción actual si detecta un obstáculo, hueco, señal o peligro inminente, emitir una alerta sonora inmediata, y luego **reanudar** la conversación o descripción que estaba dando previamente.

## Objetivos técnicos implementados
1. Implementación de motor de inferencia de modelos (YOLO/ultralytics) para identificar rápida y localmente objetos peligrosos, sumado a lectura profunda por OCR para señales de advertencia.
2. Interrupción prioritaria de audio (`critical`, `high`, `normal`), donde un nivel superior corta la reproducción de un nivel inferior.
3. El proceso de descripción normal pasa a segundo plano automáticamente ante un peligro, y se retoma (reanuda) en cuanto el peligro fue notificado.
4. Evitar repetición excesiva de alertas con la mecánica de `cooldown` por evento.
5. Organizar arquitectura por capas (`input`, `processing`, `output`) para separar la captura, la inferencia de riesgos y la salida de audio.

## Reorganizacion de carpetas
Se creo el paquete `modules/processing/` para centralizar toda la logica de procesamiento:
- `modules/processing/pipeline.py`: orquestacion del procesamiento de frame + OCR + hazard + TTS.
- `modules/processing/hazard_rules.py`: clasificacion de eventos de peligro.
- `modules/processing/hazard_detector.py`: integracion de YOLO (opcional) y reglas OCR.
- `modules/processing/__init__.py`: exporta `Processor`.

## Cambios funcionales principales
1. `AudioPlayer` ahora acepta eventos con prioridad, TTL e interrupcion.
2. `Processor` emite eventos estructurados de audio (ya no solo bytes planos).
3. Se corrigio el riesgo de duplicado de audio del pipeline normal en la implementacion reorganizada (`modules/processing/pipeline.py`).
4. Si `ultralytics` no esta disponible, el sistema sigue operando con reglas OCR.

## Archivos creados
- `modules/processing/__init__.py`
- `modules/processing/pipeline.py`
- `modules/processing/hazard_rules.py`
- `modules/processing/hazard_detector.py`
- `docs/CHANGELOG_USER.md`
- `tests/test_hazard_rules.py`
- `tests/test_audio_priority.py`
- `tests/README.md`

## Archivos modificados
- `modules/config.py`
- `modules/output/audio.py`
- `main.py`
- `requirements.txt`
- `README.md`

## Como entender el flujo
1. `main.py` captura frame y OCR.
2. `Processor` evalua peligro primero.
3. Si hay alerta, se sintetiza mensaje corto y se encola con mayor prioridad.
4. Luego se genera descripcion normal y se encola como prioridad normal.
5. `AudioPlayer` decide reproduccion segun prioridad y estado actual.

## Riesgos conocidos
- La reanudacion es por reencolado del mensaje (no resume en offset exacto del audio).
- YOLO puede requerir ajuste de umbrales/dataset para escenarios locales.

## Proximos pasos sugeridos
1. Agregar pruebas de integracion de pipeline completo.
2. Afinar reglas de peligro por contexto real de uso.
3. Medir latencia total en campo y ajustar tasa de frames.
4. Versionar reglas de peligro en archivo externo (JSON/YAML).
