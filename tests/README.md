# Tests de KODA Core

## Objetivo
Validar la logica central de alertas de peligro y el comportamiento basico del manager de audio.

## Que cubre cada prueba
- `tests/test_hazard_rules.py`
  - Verifica que palabras OCR criticas (ej. `STOP`) generen prioridad critica.
  - Verifica que objetos de riesgo (ej. `car`) se clasifiquen como prioridad alta.
- `tests/test_audio_priority.py`
  - Verifica que el `AudioPlayer` no falle cuando recibe audio vacio en `enqueue`.

## Ejecucion
```powershell
python -m pip install pytest
python -m pytest -q
```

## Nota de entorno
Estas pruebas son unitarias y ligeras. Si alguna prueba de audio depende del backend local, valida que `pygame` este instalado y funcional en tu maquina.

## Validacion manual recomendada
1. Iniciar `python main.py`.
2. Forzar texto OCR con palabra critica (`STOP`, `PELIGRO`) y confirmar interrupcion.
3. Confirmar que el flujo normal continua al terminar la alerta.
4. Confirmar que no hay spam repetido por cooldown de peligro.

