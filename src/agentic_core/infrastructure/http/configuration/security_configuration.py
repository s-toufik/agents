from dataclasses import dataclass


@dataclass(slots=True)
class SecuritySettings:
    certificate: str | None = None
