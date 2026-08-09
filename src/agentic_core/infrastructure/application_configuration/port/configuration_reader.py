from typing import Protocol

from agentic_core.infrastructure.application_configuration.model.configuration import (
    ApplicationConfiguration,
)


class ConfigurationReader(Protocol):
    def read(self) -> ApplicationConfiguration: ...
