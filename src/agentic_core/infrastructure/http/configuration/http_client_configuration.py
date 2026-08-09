from dataclasses import dataclass, field

from agentic_core.infrastructure.http.configuration.circuit_breaker_configuration import (
    CircuitBreakerSettings,
)
from agentic_core.infrastructure.http.configuration.client_configuration import ClientSettings
from agentic_core.infrastructure.http.configuration.limits_configuration import LimitsSettings
from agentic_core.infrastructure.http.configuration.retry_configuration import RetrySettings
from agentic_core.infrastructure.http.configuration.security_configuration import SecuritySettings


@dataclass(slots=True)
class HttpClientSettings:
    client_params: ClientSettings = field(default_factory=ClientSettings)
    limits: LimitsSettings = field(default_factory=LimitsSettings)
    retry: RetrySettings = field(default_factory=RetrySettings)
    circuit_breaker: CircuitBreakerSettings = field(default_factory=CircuitBreakerSettings)
    security: SecuritySettings = field(default_factory=SecuritySettings)
