from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CircuitBreakerSettings:
    recovery_timeout: int = 5
    success_threshold: int = 2
    failure_threshold: int = 3
