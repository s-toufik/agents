from functools import cached_property
from typing import Optional

from agentic.bootstrap.application_configuration import LoadApplicationConfiguration
from agentic.bootstrap.application_logger import create_logger
from agentic.infrastructure.app_configuration.model.configuration import AppConfiguration
from agentic.infrastructure.logger.port.logger import Logger


class Container:
    # -------------------------------------------------------------------------
    # Core
    # -------------------------------------------------------------------------
    def __init__(self):
        self.logging = None
        self.application_configuration = None

    @property
    async def boot(self) -> tuple[bool, Optional[Exception]]:
        try:
            self.application_configuration = self._configuration
            self.logging = self._logging
            return True, None
        except Exception as exception:
            return False, exception

    @cached_property
    def _logging(self) -> Logger:
        return create_logger(logger=None)

    @cached_property
    def _configuration(self) -> AppConfiguration:
        return LoadApplicationConfiguration(self._logging)()
