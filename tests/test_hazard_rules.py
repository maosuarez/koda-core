from modules.processing.hazard_rules import classify_hazard, PRIORITY_CRITICAL, PRIORITY_HIGH


def test_ocr_critical_keyword():
    evt = classify_hazard("Atencion STOP", None, 0.0)
    assert evt is not None
    assert evt.priority == PRIORITY_CRITICAL


def test_object_high_priority_vehicle():
    evt = classify_hazard("", "car", 0.7)
    assert evt is not None
    assert evt.priority == PRIORITY_HIGH
