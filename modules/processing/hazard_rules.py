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

    if object_name:
        obj = object_name.lower()
        if obj in {"car", "bus", "truck", "motorcycle", "bicycle"} and confidence >= 0.45:
            return HazardEvent(
                message="Atencion: vehiculo cercano detectado.",
                priority=PRIORITY_HIGH,
                source="object",
                key=f"obj_{obj}",
                ttl_seconds=3.0,
                interrupt=True,
            )
        if obj in {"traffic light", "stop sign", "person"} and confidence >= 0.4:
            return HazardEvent(
                message="Atencion: elemento de transito importante al frente.",
                priority=PRIORITY_HIGH,
                source="object",
                key=f"obj_{obj}",
                ttl_seconds=3.0,
                interrupt=True,
            )

    return None

