from typing import Protocol

from agentic.infrastructure.app_configuration.model.configuration import AppConfiguration


class ConfigurationReader(Protocol):
    def read(self) -> AppConfiguration: ...
