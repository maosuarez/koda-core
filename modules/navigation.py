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
