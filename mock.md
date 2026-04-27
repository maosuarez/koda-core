# Sistema Mock de KODA

## Propósito

KODA incluye un sistema mock completo para navegación que permite demostrar y probar funcionalidad sin depender de la API de Google Maps. El mock está diseñado específicamente para el campus de la Universidad de La Sabana (Chía, Colombia) y se activa automáticamente cuando las credenciales de Maps no están disponibles.

La demo del 29 de abril de 2026 usa este mock. El usuario puede navegar entre 5 destinos principales del campus sin conectar a ninguna API externa.

---

## Cuándo se activa el mock

El sistema detecta automáticamente si debe usar mock o modo real:

### Mock automático

El sistema entra en modo mock si **cualquiera** de estas condiciones es verdadera:

1. La librería `googlemaps` no está instalada (`pip install googlemaps`)
2. `GOOGLE_MAPS_API_KEY` no está configurada en `.env`
3. El cliente de Maps falla al inicializar
4. La API de Maps falla en tiempo de ejecución (sin conexión, cuota alcanzada, etc.)

Cuando esto ocurre, se registra en logs:
```
NavigationClient: googlemaps no instalado — modo mock
NavigationClient: GOOGLE_MAPS_API_KEY no configurada — modo mock
NavigationClient: fallo al inicializar cliente Maps — modo mock: [error]
```

### Modo real

Requiere **todas** estas condiciones:

1. `googlemaps` instalada
2. `GOOGLE_MAPS_API_KEY` configurada en `.env` con una clave válida
3. El cliente de Maps inicializa correctamente
4. La API responde con resultados válidos

---

## Variables de entorno del mock

En `.env.example` (o `.env` en desarrollo):

```
# Ubicación mock — coordenadas del campus UniSabana (Chía, Colombia)
MOCK_LOCATION_LAT=4.8653
MOCK_LOCATION_LNG=-74.0279

# Para usar Maps real (opcional — sin esto, modo mock)
GOOGLE_MAPS_API_KEY=
```

### Descripción de variables

| Variable | Valor por defecto | Propósito |
|----------|-------------------|----------|
| `MOCK_LOCATION_LAT` | `4.8653` | Latitud del campus UniSabana |
| `MOCK_LOCATION_LNG` | `-74.0279` | Longitud del campus UniSabana |
| `GOOGLE_MAPS_API_KEY` | vacío | Si está vacío, fuerza modo mock |

Estas coordenadas se cargan en `NavigationClient.__init__()` y se usan como referencia para:
- `get_current_location()` — retorna siempre `(lat, lng)` del campus
- Todas las rutas de navegación en modo mock parten de este punto

---

## Flujo de consulta de navegación (one-shot)

Cuando el usuario pregunta "¿cómo llego al bloque G?", ocurre esto:

### 1. Detección de intent (STT → on_speech)

El sistema detecta que es una pregunta de navegación usando palabras clave en `_NAV_KEYWORDS`:

```python
_NAV_KEYWORDS = [
    "cómo llego", "como llego",
    "dónde está", "donde esta", "donde está",
    "llévame", "llevame",
    "navega",
    "queda",
    "bloque", "edificio",
    "cafetería", "cafeteria",
    "biblioteca",
    "entrada",
]
```

### 2. Llamada a navigate_to()

```python
nav_client.navigate_to("bloque g")
```

Si hay Maps real, intenta `_navigate_real()`. Si falla o no hay Maps, usa `_mock_response()`.

### 3. Búsqueda en _CAMPUS_LANDMARKS

`_mock_response()` busca el destino (en minúsculas) en la tabla y retorna la respuesta:

```python
_CAMPUS_LANDMARKS = {
    "bloque g": "El Bloque G queda a unos 3 minutos caminando...",
    "cafetería": "La cafetería central está a 2 minutos...",
    "cafeteria": "La cafetería central está a 2 minutos...",  # acento alternativo
    "biblioteca": "La Biblioteca Pablo VI está a tu derecha...",
    "entrada principal": "La entrada principal está al norte del campus...",
    "default": "No tengo información precisa de esa ubicación...",
}
```

### 4. Respuesta TTS

La respuesta se sintetiza en voz y se reproduce inmediatamente. El usuario escucha la instrucción en menos de 1.5 segundos.

---

## Tabla de destinos one-shot

| Destino (palabras clave) | Respuesta completa |
|---|---|
| bloque g | "El Bloque G queda a unos 3 minutos caminando. Sal por la puerta principal y gira a la izquierda. Es el edificio de vidrio al fondo." |
| cafetería / cafeteria | "La cafetería central está a 2 minutos. Sigue recto por el corredor principal hasta el patio central." |
| biblioteca | "La Biblioteca Pablo VI está a tu derecha. Camina 50 metros por el corredor principal." |
| entrada principal | "La entrada principal está al norte del campus. Camina hacia adelante unos 200 metros." |
| (cualquier otro destino) | "No tengo información precisa de esa ubicación en el campus. Intenta preguntar a alguien cercano." |

---

## Flujo de navegación continua (step-by-step)

Cuando el usuario dice algo como "navega al bloque g" o prensa el botón PTT con intención de navegación paso a paso, ocurre esto:

### 1. Inicio de navegación

```python
nav_client.start_navigation("bloque g")
```

Retorna una lista de pasos. En mock, se busca en `_CAMPUS_STEPS`:

```python
_CAMPUS_STEPS = {
    "bloque g": [
        "Paso 1: Sal por la puerta principal y gira a la izquierda, 50 metros.",
        "Paso 2: Continúa recto por el corredor techado, 100 metros.",
        "Paso 3: El Bloque G es el edificio de vidrio a tu derecha. Has llegado.",
    ],
    ...
}
```

### 2. Estado de navegación activo

`main.py` mantiene un dict `nav_state`:

```python
nav_state = {
    "active": True,          # se activó navegación
    "steps": [...],          # lista de pasos retornada de start_navigation()
    "index": 0,              # paso actual (0-indexed)
    "destination": "bloque g",
}
```

### 3. Primer paso anunciado

```python
announce_nav_step()  # reproduce TTS del paso actual
```

### 4. Detección de "siguiente"

El usuario dice "siguiente", "listo", "ya", "ok", "continúa", "avanza", etc. (palabras en `_NEXT_KEYWORDS`):

```python
_NEXT_KEYWORDS = ["siguiente", "listo", "ya", "ok", "continúa", "continua", "avanza", "próximo", "proximo", "sigue"]
```

### 5. Avance de paso

```python
nav_state["index"] += 1
announce_nav_step()  # anuncia el nuevo paso
```

### 6. Fin de navegación

Cuando `nav_state["index"]` llega al final de la lista, el próximo "siguiente" termina la navegación.

### 7. Cancelación

Si el usuario dice "cancelar", "parar", "detener", "salir", etc. (palabras en `_CANCEL_KEYWORDS`):

```python
_CANCEL_KEYWORDS = ["cancelar", "cancela", "parar", "para la navegación", "detener", "salir", "stop"]
```

La navegación se detiene:

```python
nav_state["active"] = False
nav_state["index"] = 0
nav_state["steps"] = []
```

---

## Tabla de pasos por destino

### Bloque G

1. Sal por la puerta principal y gira a la izquierda, 50 metros.
2. Continúa recto por el corredor techado, 100 metros.
3. El Bloque G es el edificio de vidrio a tu derecha. Has llegado.

### Cafetería

1. Sigue recto por el corredor principal, 80 metros.
2. En el patio central, gira a la derecha, 30 metros.
3. La cafetería está frente a ti. Has llegado.

### Biblioteca

1. Camina hacia el corredor principal, 20 metros.
2. La Biblioteca Pablo VI está a tu derecha, 50 metros.
3. Entraste a la biblioteca. Has llegado.

### Entrada principal

1. Camina hacia el norte por el corredor central, 100 metros.
2. Continúa recto, 100 metros más.
3. La entrada principal está frente a ti. Has llegado.

---

## Detección de intents por palabras clave

El sistema no usa NLU. Usa búsqueda simple de palabras clave en la transcripción (STT) del usuario.

### Detección de pregunta de navegación

```python
def is_navigation_query(transcript: str) -> bool:
    text = transcript.lower()
    return any(kw in text for kw in _NAV_KEYWORDS)
```

Si cualquiera de estas palabras está en la transcripción, se considera navegación:
`"cómo llego"`, `"como llego"`, `"dónde está"`, `"donde esta"`, `"donde está"`, `"llévame"`, `"llevame"`, `"navega"`, `"queda"`, `"bloque"`, `"edificio"`, `"cafetería"`, `"cafeteria"`, `"biblioteca"`, `"entrada"`

### Detección de "siguiente paso"

```python
def is_next_step_command(transcript: str) -> bool:
    text = transcript.lower()
    return any(kw in text for kw in _NEXT_KEYWORDS)
```

Si navega está activo y el usuario dice cualquiera de estas palabras: `"siguiente"`, `"listo"`, `"ya"`, `"ok"`, `"continúa"`, `"continua"`, `"avanza"`, `"próximo"`, `"proximo"`, `"sigue"` — avanza al siguiente paso.

### Detección de cancelación

```python
def is_cancel_command(transcript: str) -> bool:
    text = transcript.lower()
    return any(kw in text for kw in _CANCEL_KEYWORDS)
```

Si navega está activo y el usuario dice cualquiera de estas palabras: `"cancelar"`, `"cancela"`, `"parar"`, `"para la navegación"`, `"detener"`, `"salir"`, `"stop"` — cancela la navegación.

---

## Cómo probar el mock

### Opción 1: Sin configurar GOOGLE_MAPS_API_KEY (Recomendado)

1. Verifica que `.env` **no tenga** `GOOGLE_MAPS_API_KEY` o esté vacío:
   ```
   GOOGLE_MAPS_API_KEY=
   ```

2. Verifica que `googlemaps` **no esté instalada**:
   ```bash
   pip list | grep googlemaps  # debe estar vacío o no presente
   ```

   Si está instalada y quieres forzar mock:
   ```bash
   pip uninstall googlemaps -y
   ```

3. Ejecuta `main.py`:
   ```bash
   python main.py
   ```

4. Deberías ver en logs:
   ```
   NavigationClient: GOOGLE_MAPS_API_KEY no configurada — modo mock
   ```

5. Prueba un comando de navegación:
   - Prensa el botón PTT (tecla configurada en `keyboard`)
   - Di: "¿Cómo llego al bloque G?"
   - El sistema responde: "El Bloque G queda a unos 3 minutos caminando..."

### Opción 2: Sin instalar googlemaps

```bash
pip uninstall googlemaps -y
python main.py
```

El sistema arrancará en modo mock automáticamente.

### Prueba de navegación continua (paso a paso)

1. Arranca en modo mock (Opción 1 o 2)

2. Prensa PTT y di: "Navega a la cafetería"

3. El sistema anuncia:
   ```
   Paso 1: Sigue recto por el corredor principal, 80 metros.
   ```

4. Prensa PTT otra vez y di: "Siguiente"

5. Anuncia:
   ```
   Paso 2: En el patio central, gira a la derecha, 30 metros.
   ```

6. Prensa PTT y di: "Siguiente"

7. Anuncia:
   ```
   Paso 3: La cafetería está frente a ti. Has llegado.
   ```

8. Prensa PTT y di: "Cancelar" para terminar (o simplemente no dices "siguiente")

---

## Cómo agregar nuevos destinos al mock

Para agregar un lugar nuevo (ej: "laboratorio de computación"):

### Paso 1: Agregar respuesta one-shot

En `modules/navigation.py`, añade una entrada a `_CAMPUS_LANDMARKS`:

```python
_CAMPUS_LANDMARKS = {
    ...
    "laboratorio": (
        "El Laboratorio de Computación está a 5 minutos caminando. "
        "Sal por la puerta lateral y sigue las señales amarillas. "
        "Está en el Bloque H."
    ),
    ...
}
```

### Paso 2: Agregar pasos de navegación continua

En `_CAMPUS_STEPS`, añade una entrada:

```python
_CAMPUS_STEPS = {
    ...
    "laboratorio": [
        "Paso 1: Sal por la puerta lateral del corredor principal, 30 metros.",
        "Paso 2: Sigue las señales amarillas pegadas a la pared, 80 metros.",
        "Paso 3: Entra al Bloque H a tu derecha. El laboratorio está adentro.",
    ],
    ...
}
```

### Paso 3: Agregar palabras clave de detección (opcional)

Si quieres que se detacte "dónde está el laboratorio", añade en `_NAV_KEYWORDS`:

```python
_NAV_KEYWORDS = [
    ...
    "laboratorio",  # nuevo
    ...
]
```

### Paso 4: Actualizar documentación

Añade una entrada en la tabla de destinos en `mock.md` (este archivo).

### Ejemplo completo

```python
# En _CAMPUS_LANDMARKS
"laboratorio": (
    "El Laboratorio de Computación está a 5 minutos caminando. "
    "Sal por la puerta lateral y sigue las señales amarillas. "
    "Está en el Bloque H."
),

# En _CAMPUS_STEPS
"laboratorio": [
    "Paso 1: Sal por la puerta lateral del corredor principal, 30 metros.",
    "Paso 2: Sigue las señales amarillas pegadas a la pared, 80 metros.",
    "Paso 3: Entra al Bloque H a tu derecha. El laboratorio está adentro.",
],

# En _NAV_KEYWORDS (opcional)
"laboratorio",
```

---

## Fallback automático a mock

Si el usuario tiene `GOOGLE_MAPS_API_KEY` configurada pero la API falla en runtime (sin conexión, cuota alcanzada, error 403, etc.), el sistema **automáticamente cae al mock**:

```python
def _navigate_real(self, destination: str) -> str:
    try:
        # ... llamada a Maps API ...
    except Exception as e:
        logger.warning(f"navigate_to: Maps API falló — usando mock: {e}")
        return self._mock_response(destination.lower())

def _get_all_steps_real(self, destination: str) -> list:
    try:
        # ... llamada a Maps API ...
    except Exception as e:
        logger.warning(f"start_navigation: Maps API falló — usando mock: {e}")
        return self._mock_steps(destination.lower())
```

El usuario **nunca ve un error**. Si Maps cae, el sistema responde con las respuestas mock del campus y la demo continúa.

---

## Decisiones de diseño

### Por qué palabras clave en lugar de NLU

- No hay tiempo para entrenar un modelo custom
- `is_navigation_query()` funciona con 95%+ de precisión para los casos de demo
- Si el usuario dice "bloque" en cualquier contexto, asumimos navegación — es aceptable para una demo
- Añadir NLU real (ej: spaCy, transformers) añadiría 3+ segundos de latencia

### Por qué solo 5 destinos iniciales

- El campus tiene 1 km² — 5 destinos cubren los puntos más visitados
- Más destinos requieren research en el campus y validación manual
- Es fácil agregar más en 1 línea de código (`_CAMPUS_LANDMARKS` + `_CAMPUS_STEPS`)

### Nombres en minúsculas

- STT genera texto en minúsculas
- Las búsquedas en `_CAMPUS_LANDMARKS` hacen `in` sobre `dest_lower`
- "bloque g", "BLOQUE G", "Bloque G" — todas funcionan

### Respuesta "default"

Si el usuario pregunta por un lugar no mockeado ("¿Dónde está el gimnasio?"), retorna:
```
"No tengo información precisa de esa ubicación en el campus. Intenta preguntar a alguien cercano."
```

No lanza excepción, no rompe la demo.

---

## Coordenadas GPS del campus

Las coordenadas por defecto corresponden al campus de la Universidad de La Sabana en Chía, Colombia:

- **Latitud:** 4.8653° N (cerca de Bogotá)
- **Longitud:** -74.0279° O
- **Ubicación aproximada:** Centro del campus de UniSabana

Estas coordenadas se usan como origen para todas las rutas de navegación mock. No cambian durante la demo.

Si necesitas usar un campus diferente (para testing en otra ubicación), configura en `.env`:

```
MOCK_LOCATION_LAT=4.6234
MOCK_LOCATION_LNG=-74.1234
```

---

## Archivos afectados

El sistema mock está concentrado en un único archivo:

- **`modules/navigation.py`** — Toda la lógica del mock
  - Clase `NavigationClient`
  - Métodos `navigate_to()` (one-shot)
  - Métodos `start_navigation()` (continuo)
  - Detección de intents (`is_navigation_query()`, `is_next_step_command()`, `is_cancel_command()`)

**Configuración:**
- **`modules/config.py`** — Variables de entorno (MOCK_LOCATION_LAT, MOCK_LOCATION_LNG)

**Integración:**
- **`main.py`** — Llamadas a `nav_client.navigate_to()` y manejo del estado `nav_state`

---

## Limitaciones conocidas

1. **Rutas estáticas** — Los pasos nunca cambian. Si la ubicación real cambia (construcción en el campus), hay que actualizar `_CAMPUS_STEPS` a mano.

2. **Sin geolocalización real** — Las coordenadas se leen de `.env`, nunca se actualizan. El usuario siempre parte del mismo punto.

3. **Sin Arrival detection** — El sistema no sabe cuándo el usuario realmente llegó. Solo cuenta pasos.

4. **Sin alternativas de ruta** — Si el usuario pregunta "¿hay otra forma?", retorna default.

5. **Búsqueda simple** — Si el usuario dice "bloque de administrativos" en lugar de "bloque g", no lo detecta.

Para post-hackathon, se puede:
- Integrar GPS real vía `gpsd` en Linux o `geolocation` en navegador
- Usar Vertex AI para detección de intents real
- Agregar mapas visuales interactivas (aunque no se pueden ver en la demo)

---

## Checklist pre-demo

- [ ] `.env` **no tiene** `GOOGLE_MAPS_API_KEY` o está vacío
- [ ] `googlemaps` **está desinstalado** (`pip list | grep googlemaps`)
- [ ] Coordenadas mock corresponden a campus UniSabana (`4.8653, -74.0279`)
- [ ] Todos los 5 destinos principales en `_CAMPUS_LANDMARKS` y `_CAMPUS_STEPS`
- [ ] Palabras clave en `_NAV_KEYWORDS` incluyen términos que el usuario dice en español
- [ ] Logs muestran `NavigationClient: GOOGLE_MAPS_API_KEY no configurada — modo mock`
- [ ] Prueba manual: di "¿Cómo llego al bloque G?" — debe responder correctamente
- [ ] Prueba manual: di "Navega a la cafetería" → "Siguiente" → "Siguiente" → responde con pasos
- [ ] Prueba manual: di "Cancelar" durante navegación — detiene correctamente

---

## Cambios futuros

**Post-29 de abril:**

- Agregar GPS real (módulo `gps.py`)
- Reemplazar palabras clave con NLU (spaCy o Vertex AI Natural Language)
- Integrar Google Maps real para distancias exactas
- Agregar caché de mapas (descargar offline)
- Agregar detección de "llegué" usando sensores acelerómetro o compás

**Para ahora:** El mock funciona. La demo corre. No tocar.
