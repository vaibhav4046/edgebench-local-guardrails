from edgebench.runner.determinism import hash_normalized_json


def test_normalized_hash_ignores_key_order():
    a = {"answer": "ok", "category": "qa", "confidence": 0.5, "key_points": ["x"]}
    b = {"key_points": ["x"], "confidence": 0.5, "category": "qa", "answer": "ok"}
    assert hash_normalized_json(a) == hash_normalized_json(b)
