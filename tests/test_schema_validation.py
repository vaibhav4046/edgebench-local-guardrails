from edgebench.schema.validator import parse_json_object, validate_canonical_output, validation_errors


def test_schema_validation_passes_for_valid_payload():
    payload = {
        "answer": "ok",
        "category": "qa",
        "confidence": 0.7,
        "key_points": ["a", "b"],
    }
    model = validate_canonical_output(payload)
    assert model.answer == "ok"


def test_schema_validation_rejects_extra_keys():
    payload = {
        "answer": "ok",
        "category": "qa",
        "confidence": 0.7,
        "key_points": ["a"],
        "extra": "not allowed",
    }
    errors = validation_errors(payload)
    assert errors


def test_parse_json_object_rejects_non_object():
    try:
        parse_json_object("[]")
    except Exception:
        return
    raise AssertionError("Expected parse_json_object to fail for non-object JSON")
