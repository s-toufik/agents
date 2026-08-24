from typing import Protocol, Optional

from fastapi import APIRouter

from agentic_core.infrastructure.application_configuration.model.configuration import (
    ApplicationConfiguration,
)
from agentic_core.infrastructure.logger.port.logger import Logger


class Container(Protocol):

    @property
    def logging(self) -> Logger: ...

    @property
    def application_configuration(self) -> ApplicationConfiguration: ...

    @property
    async def create_routers(self) -> list[APIRouter]: ...

    @property
    async def boot(self) -> tuple[bool, Optional[Exception]]: ...

    async def start(self) -> None: ...
    async def stop(self) -> None: ...
