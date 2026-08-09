from typing import Protocol

from agentic_core.infrastructure.application_configuration.model.configuration import (
    ApplicationConfiguration,
)


class Configuration(Protocol):
    def load(self) -> ApplicationConfiguration | None: ...

    def reload(self) -> ApplicationConfiguration | None: ...
