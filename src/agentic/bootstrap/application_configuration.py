import os
from typing import Optional

import dotenv
from pathlib import Path

from agentic.bootstrap.application_logger import create_logger
from agentic.infrastructure.app_configuration.adapter.load_configuration import LoadConfiguration
from agentic.infrastructure.app_configuration.adapter.omega_configuration_reader import (
    OmegaConfigurationReader,
)
from agentic.infrastructure.app_configuration.enum.run_type_environment import RunTypeEnvironment
from agentic.infrastructure.app_configuration.model.configuration import AppConfiguration
from agentic.infrastructure.app_configuration.port.configuration import Configuration
from agentic.infrastructure.app_configuration.port.configuration_reader import ConfigurationReader
from agentic.infrastructure.logger.port.logger import Logger


class LoadApplicationConfiguration:
    def __init__(self, logger: Optional[Logger] = None):
        self._logger = create_logger(logger)

    def __call__(self, *args, **kwargs) -> AppConfiguration:
        dotenv.load_dotenv()
        run_type_environment: RunTypeEnvironment = RunTypeEnvironment(os.getenv("APP_ENV", "dev"))
        configuration_directory: Path = Path(os.getenv("CONFIGURATION_DIR", ""))

        self._logger.info(f"Loading configuration for {run_type_environment} environment")
        if not configuration_directory:
            exception = FileNotFoundError("No configuration file path provided")
            self._logger.critical(exception.__str__())
            raise exception

        configuration_reader: ConfigurationReader = OmegaConfigurationReader(
            run_type_environment, configuration_directory
        )

        configuration_loader: Configuration = LoadConfiguration(configuration_reader, self._logger)
        configuration = configuration_loader.load()
        if not configuration:
            exception = ValueError("No configuration loaded")
            self._logger.critical(exception.__str__())
            raise ValueError("No configuration loaded")

        return configuration
