from typing import Protocol

from fastapi import APIRouter
from pycraftcore.application_configuration import ApplicationConfiguration
from pycraftcore.logger.port import Logger


class Container(Protocol):
    @property
    def logging(self) -> Logger: ...

    @property
    def application_configuration(self) -> ApplicationConfiguration: ...

    @property
    async def create_routers(self) -> list[APIRouter]: ...

    @property
    async def boot(self) -> tuple[bool, Exception | None]: ...

    async def start(self) -> None: ...
    async def stop(self) -> None: ...
