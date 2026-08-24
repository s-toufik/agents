from agentic_core.infrastructure.http.configuration.circuit_breaker_configuration import (
    CircuitBreakerSettings,
)
from agentic_core.infrastructure.http.configuration.client_configuration import ClientSettings
from agentic_core.infrastructure.http.configuration.http_client_configuration import (
    HttpClientSettings,
)
from agentic_core.infrastructure.http.configuration.limits_configuration import LimitsSettings
from agentic_core.infrastructure.http.configuration.security_configuration import SecuritySettings


def test_circuit_breaker_settings_defaults():
    settings = CircuitBreakerSettings()

    assert settings.recovery_timeout == 5
    assert settings.success_threshold == 2
    assert settings.failure_threshold == 3


def test_client_settings_default_base_url_is_empty():
    assert ClientSettings().base_url == ""


def test_limits_settings_defaults():
    settings = LimitsSettings()

    assert settings.timeout == 30
    assert settings.max_connections == 1000
    assert settings.max_connections_per_host == 100


def test_security_settings_default_certificate_is_none():
    assert SecuritySettings().certificate is None


def test_http_client_settings_builds_all_sub_settings_by_default():
    settings = HttpClientSettings()

    assert isinstance(settings.client_params, ClientSettings)
    assert isinstance(settings.limits, LimitsSettings)
    assert isinstance(settings.circuit_breaker, CircuitBreakerSettings)
    assert isinstance(settings.security, SecuritySettings)
    assert settings.retry.retry_on == (Exception,)
