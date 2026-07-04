"""Testes — retry com backoff."""

import pytest

from src.retry import retry_call


class TestRetry:
    def test_succeeds_first_try(self):
        assert retry_call(lambda: 42) == 42

    def test_retries_then_succeeds(self):
        calls = {"n": 0}

        def flaky() -> str:
            calls["n"] += 1
            if calls["n"] < 3:
                raise ValueError("fail")
            return "ok"

        assert retry_call(flaky, base_delay=0.01, exceptions=(ValueError,)) == "ok"
        assert calls["n"] == 3

    def test_raises_after_max_attempts(self):
        with pytest.raises(RuntimeError):
            retry_call(lambda: (_ for _ in ()).throw(RuntimeError("x")), max_attempts=2, base_delay=0.01)
