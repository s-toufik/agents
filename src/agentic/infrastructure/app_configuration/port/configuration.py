from typing import Protocol

from agentic.infrastructure.app_configuration.model.configuration import AppConfiguration


class Configuration(Protocol):
    def load(self) -> AppConfiguration | None: ...

    def reload(self) -> AppConfiguration | None: ...
