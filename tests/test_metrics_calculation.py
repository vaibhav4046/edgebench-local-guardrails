from edgebench.runner.retry_pipeline import _compute_tokens_per_second


def test_tokens_per_second_formula():
    # 250 tokens over 2 seconds => 125 tokens/sec.
    tokens = _compute_tokens_per_second(250, 2_000_000_000)
    assert tokens == 125.0


def test_tokens_per_second_none_for_zero_duration():
    assert _compute_tokens_per_second(100, 0) is None
