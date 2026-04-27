import logging
import re

from modules.config import get_env_variable

logger = logging.getLogger(__name__)

# Intentar importar googlemaps; si no está instalado, modo mock automático
try:
    import googlemaps
    _GOOGLEMAPS_AVAILABLE = True
except ImportError:
    _GOOGLEMAPS_AVAILABLE = False

# Palabras clave para detectar preguntas de navegación
_NAV_KEYWORDS = [
    "cómo llego", "como llego",
    "dónde está", "donde esta", "donde está",
    "llévame", "llevame",
    "navega",
    "queda",
    "bloque",
    "edificio",
    "cafetería", "cafeteria",
    "biblioteca",
    "entrada",
]

# Respuestas mock para lugares conocidos del campus UniSabana
_CAMPUS_LANDMARKS = {
    "bloque g": (
        "El Bloque G queda a unos 3 minutos caminando. "
        "Sal por la puerta principal y gira a la izquierda. "
        "Es el edificio de vidrio al fondo."
    ),
    "cafetería": (
        "La cafetería central está a 2 minutos. "
        "Sigue recto por el corredor principal hasta el patio central."
    ),
    "cafeteria": (
        "La cafetería central está a 2 minutos. "
        "Sigue recto por el corredor principal hasta el patio central."
    ),
    "biblioteca": (
        "La Biblioteca Pablo VI está a tu derecha. "
        "Camina 50 metros por el corredor principal."
    ),
    "entrada principal": (
        "La entrada principal está al norte del campus. "
        "Camina hacia adelante unos 200 metros."
    ),
    "default": (
        "No tengo información precisa de esa ubicación en el campus. "
        "Intenta preguntar a alguien cercano."
    ),
}

# Patrón para limpiar etiquetas HTML que devuelve la API de Maps
_HTML_TAG = re.compile(r"<[^>]+>")

# Pasos mock por destino para modo navegación continua
_CAMPUS_STEPS = {
    "bloque g": [
        "Paso 1: Sal por la puerta principal y gira a la izquierda, 50 metros.",
        "Paso 2: Continúa recto por el corredor techado, 100 metros.",
        "Paso 3: El Bloque G es el edificio de vidrio a tu derecha. Has llegado.",
    ],
    "cafetería": [
        "Paso 1: Sigue recto por el corredor principal, 80 metros.",
        "Paso 2: En el patio central, gira a la derecha, 30 metros.",
        "Paso 3: La cafetería está frente a ti. Has llegado.",
    ],
    "cafeteria": [
        "Paso 1: Sigue recto por el corredor principal, 80 metros.",
        "Paso 2: En el patio central, gira a la derecha, 30 metros.",
        "Paso 3: La cafetería está frente a ti. Has llegado.",
    ],
    "biblioteca": [
        "Paso 1: Camina hacia el corredor principal, 20 metros.",
        "Paso 2: La Biblioteca Pablo VI está a tu derecha, 50 metros.",
        "Paso 3: Entraste a la biblioteca. Has llegado.",
    ],
    "entrada principal": [
        "Paso 1: Camina hacia el norte por el corredor central, 100 metros.",
        "Paso 2: Continúa recto, 100 metros más.",
        "Paso 3: La entrada principal está frente a ti. Has llegado.",
    ],
}

_NEXT_KEYWORDS = ["siguiente", "listo", "ya", "ok", "continúa", "continua", "avanza", "próximo", "proximo", "sigue"]
_CANCEL_KEYWORDS = ["cancelar", "cancela", "parar", "para la navegación", "detener", "salir", "stop"]


class NavigationClient:
    def __init__(self):
        api_key = get_env_variable("GOOGLE_MAPS_API_KEY")
        lat = float(get_env_variable("MOCK_LOCATION_LAT", "4.8653"))
        lng = float(get_env_variable("MOCK_LOCATION_LNG", "-74.0279"))
        self._mock_lat = lat
        self._mock_lng = lng

        self._maps_client = None
        if api_key and _GOOGLEMAPS_AVAILABLE:
            try:
                self._maps_client = googlemaps.Client(key=api_key)
                logger.info("NavigationClient: modo Maps real")
            except Exception as e:
                logger.warning(f"NavigationClient: fallo al inicializar cliente Maps — modo mock: {e}")
        elif not _GOOGLEMAPS_AVAILABLE:
            logger.info("NavigationClient: googlemaps no instalado — modo mock")
        else:
            logger.info("NavigationClient: GOOGLE_MAPS_API_KEY no configurada — modo mock")

    def get_current_location(self) -> tuple:
        # Coordenadas mock desde .env; en el futuro reemplazar con GPS real o geolocalización por IP
        return (self._mock_lat, self._mock_lng)

    def navigate_to(self, destination: str) -> str:
        """Retorna instrucciones de navegación en español. Nunca lanza excepción."""
        if self._maps_client is not None:
            return self._navigate_real(destination)
        return self._mock_response(destination.lower())

    def is_navigation_query(self, transcript: str) -> bool:
        text = transcript.lower()
        return any(kw in text for kw in _NAV_KEYWORDS)

    # ── privados ────────────────────────────────────────────────────────────────

    def _navigate_real(self, destination: str) -> str:
        try:
            origin = self.get_current_location()
            result = self._maps_client.directions(
                origin=origin,
                destination=destination,
                mode="walking",
                language="es",
            )
            if not result:
                return self._mock_response(destination.lower())

            steps = result[0].get("legs", [{}])[0].get("steps", [])
            if not steps:
                return self._mock_response(destination.lower())

            # Máximo 2 pasos — el usuario no puede memorizar más
            parts = []
            for step in steps[:2]:
                raw = step.get("html_instructions", "")
                clean = _HTML_TAG.sub("", raw).strip()
                distance = step.get("distance", {}).get("text", "")
                if distance:
                    clean = f"{clean}, {distance}"
                if clean:
                    parts.append(clean)

            return ". ".join(parts) + "." if parts else self._mock_response(destination.lower())
        except Exception as e:
            logger.warning(f"navigate_to: Maps API falló — usando mock: {e}")
            return self._mock_response(destination.lower())

    def _mock_response(self, dest_lower: str) -> str:
        for landmark, response in _CAMPUS_LANDMARKS.items():
            if landmark != "default" and landmark in dest_lower:
                return response
        return _CAMPUS_LANDMARKS["default"]

    # ── navegación continua ─────────────────────────────────────────────────────

    def start_navigation(self, destination: str) -> list:
        """Retorna todos los pasos de navegación como lista. Nunca lanza excepción."""
        if self._maps_client is not None:
            return self._get_all_steps_real(destination)
        return self._mock_steps(destination.lower())

    def is_next_step_command(self, transcript: str) -> bool:
        text = transcript.lower()
        return any(kw in text for kw in _NEXT_KEYWORDS)

    def is_cancel_command(self, transcript: str) -> bool:
        text = transcript.lower()
        return any(kw in text for kw in _CANCEL_KEYWORDS)

    def _get_all_steps_real(self, destination: str) -> list:
        try:
            origin = self.get_current_location()
            result = self._maps_client.directions(
                origin=origin,
                destination=destination,
                mode="walking",
                language="es",
            )
            if not result:
                return self._mock_steps(destination.lower())
            steps = result[0].get("legs", [{}])[0].get("steps", [])
            parts = []
            for i, step in enumerate(steps, 1):
                raw = step.get("html_instructions", "")
                clean = _HTML_TAG.sub("", raw).strip()
                distance = step.get("distance", {}).get("text", "")
                if distance:
                    clean = f"{clean}, {distance}"
                if clean:
                    parts.append(f"Paso {i}: {clean}")
            return parts if parts else self._mock_steps(destination.lower())
        except Exception as e:
            logger.warning(f"start_navigation: Maps API falló — usando mock: {e}")
            return self._mock_steps(destination.lower())

    def _mock_steps(self, dest_lower: str) -> list:
        for landmark, steps in _CAMPUS_STEPS.items():
            if landmark in dest_lower:
                return list(steps)
        return ["No tengo información de esa ubicación. Intenta preguntar a alguien cercano."]
