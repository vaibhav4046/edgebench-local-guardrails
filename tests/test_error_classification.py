from edgebench.errors import JsonParseError, OllamaError, SchemaError, TimeoutError
from edgebench.runner.retry_pipeline import classify_exception


def test_error_classification_mapping():
    assert classify_exception(JsonParseError("x")).value == "JSON_PARSE_ERROR"
    assert classify_exception(SchemaError("x")).value == "SCHEMA_VALIDATION_ERROR"
    assert classify_exception(TimeoutError("x")).value == "TIMEOUT"
    assert classify_exception(OllamaError("x")).value == "OLLAMA_ERROR"
