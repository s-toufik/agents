from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from agentic_application.bootstrap.dependency_injection.base.base import BaseDI

_TELEMETRY_PATCH_TARGET = (
    "agentic_application.bootstrap.dependency_injection.base.base.OpenTelemetryProvider"
)


def make_di_with_config(env: str = "debug") -> BaseDI:
    di = BaseDI()
    # Bypass the real (YAML-backed) _configuration cached_property -- _telemetry_provider
    # only needs .env, so seed the cache directly rather than loading full app config.
    di.__dict__["_configuration"] = SimpleNamespace(env=env)
    return di


def test_telemetry_provider_is_constructed_once_and_reused():
    di = make_di_with_config()
    with patch(_TELEMETRY_PATCH_TARGET) as mock_provider_cls:
        mock_provider_cls.return_value = MagicMock()

        first = di._telemetry_provider
        second = di._telemetry_provider

        assert first is second
        mock_provider_cls.assert_called_once()


def test_telemetry_provider_uses_the_configured_environment():
    di = make_di_with_config(env="deploy")
    with patch(_TELEMETRY_PATCH_TARGET) as mock_provider_cls:
        mock_provider_cls.return_value = MagicMock()

        _ = di._telemetry_provider

        mock_provider_cls.assert_called_once_with(
            service_name="risk-analytics", environment="deploy"
        )


@pytest.mark.asyncio
async def test_shutdown_telemetry_shuts_down_and_evicts_the_cached_provider():
    di = make_di_with_config()
    with patch(_TELEMETRY_PATCH_TARGET) as mock_provider_cls:
        provider = MagicMock()
        mock_provider_cls.return_value = provider

        _ = di._telemetry_provider
        await di._shutdown_telemetry()

        provider.shutdown.assert_called_once()
        assert "_telemetry_provider" not in di.__dict__


@pytest.mark.asyncio
async def test_shutdown_telemetry_is_a_no_op_when_the_provider_was_never_built():
    di = make_di_with_config()

    await di._shutdown_telemetry()  # must not raise, must not construct a provider
