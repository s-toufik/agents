import os

import dotenv
from pathlib import Path

from pycraftcore.application_configuration import (
    ApplicationConfiguration,
    ConfigurationReader,
    Configuration,
)
from pycraftcore.application_configuration.adapter import (
    OmegaConfigurationReader,
    LoadApplicationConfiguration,
)
from pycraftcore.application_configuration.enum import RunTypeEnvironment
from pycraftcore.logger.port import Logger

from agentic_application.bootstrap.configuration.application_logger import create_logger


class SetApplicationConfiguration:
    def __init__(self, logger: Logger | None = None):
        self._logger = create_logger(logger)

    def __call__(self, *args, **kwargs) -> ApplicationConfiguration:
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

        configuration_loader: Configuration = LoadApplicationConfiguration(
            configuration_reader, self._logger
        )
        configuration = configuration_loader.load()
        if not configuration:
            exception = ValueError("No configuration loaded")
            self._logger.critical(exception.__str__())
            raise ValueError("No configuration loaded")

        return configuration
