from dataclasses import dataclass
from typing import Optional


PRIORITY_CRITICAL = 0
PRIORITY_HIGH = 1
PRIORITY_NORMAL = 2


@dataclass
class HazardEvent:
    message: str
    priority: int
    source: str
    key: str
    ttl_seconds: float = 3.0
    interrupt: bool = True


def classify_hazard(ocr_text: str, object_name: Optional[str], confidence: float) -> Optional[HazardEvent]:
    text = (ocr_text or "").upper()
    critical_keywords = ("STOP", "ALTO", "PELIGRO", "NO PASE", "EMERGENCIA")

    if any(k in text for k in critical_keywords):
        return HazardEvent(
            message="Alerta critica: senal de riesgo detectada.",
            priority=PRIORITY_CRITICAL,
            source="ocr",
            key="ocr_critical",
            ttl_seconds=4.0,
            interrupt=True,
        )

    return None

