from functools import cached_property


from agentic_application.bootstrap.configuration.application_configuration import (
    LoadApplicationConfiguration,
)
from agentic_application.bootstrap.configuration.application_logger import create_logger
from agentic_core.infrastructure.application_configuration.model.configuration import (
    ApplicationConfiguration,
)
from agentic_core.infrastructure.http.port.async_http_client import AsyncHttpFactory
from agentic_core.infrastructure.logger.adapter.loguru_logger import LoguruLogger
from agentic_core.infrastructure.logger.port.logger import Logger
from agentic_core.infrastructure.repository.repository import RepositoryFactory


class BaseDI:
    def __init__(self):
        self._clients: list[AsyncHttpFactory] = []
        self._repositories: list[RepositoryFactory] = []

    def _register_client(self, client: AsyncHttpFactory) -> AsyncHttpFactory:
        self._clients.append(client)
        return client

    def _register_repository(self, repository: RepositoryFactory) -> RepositoryFactory:
        self._repositories.append(repository)
        return repository

    async def _switch_factories(self, mode: str) -> None:
        if mode.lower() == "on":
            for client in self._clients:
                if hasattr(client, "start"):
                    await client.start()
            for repository in self._repositories:
                if hasattr(repository, "connect"):
                    await repository.connect()
        elif mode.lower() == "off":
            for client in self._clients:
                if hasattr(client, "close"):
                    await client.close()
            for repository in self._repositories:
                if hasattr(repository, "disconnect"):
                    await repository.disconnect()
        else:
            raise ValueError(f"Invalid mode: {mode}")

    @cached_property
    def _logging(self) -> Logger:
        return create_logger(logger=LoguruLogger())

    @cached_property
    def _configuration(self) -> ApplicationConfiguration:
        return LoadApplicationConfiguration(self._logging)()
