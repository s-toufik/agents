import pytest

from agentic_core.infrastructure.http.configuration.retry_configuration import RetrySettings


def test_defaults_are_valid():
    settings = RetrySettings()

    assert settings.retry_count == 4
    assert settings.retry_delay == 5
    assert settings.retry_on == (Exception,)


def test_empty_retry_on_raises_runtime_error():
    with pytest.raises(RuntimeError):
        RetrySettings(retry_on=())
