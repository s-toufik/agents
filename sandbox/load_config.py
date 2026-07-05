import os
import dotenv
from pathlib import Path
from pprint import pprint

from agentic.infrastructure.app_configuration.adapter.load_configuration import (
    LoadConfiguration,
)
from agentic.infrastructure.app_configuration.adapter.omega_configuration_reader import (
    OmegaConfigurationReader,
)
from agentic.infrastructure.app_configuration.enum.run_type_environment import (
    RunTypeEnvironment,
)
from agentic.infrastructure.app_configuration.model.configuration import AppConfiguration
from agentic.infrastructure.app_configuration.port.configuration import Configuration
from agentic.infrastructure.app_configuration.port.configuration_reader import (
    ConfigurationReader,
)
from agentic.infrastructure.logger.adapter.loguru_logger import LoguruLogger
from agentic.infrastructure.logger.port.logger import Logger

logger: Logger = LoguruLogger()
def load_application_configuration() -> AppConfiguration:
    dotenv.load_dotenv()
    run_type_environment: RunTypeEnvironment = RunTypeEnvironment(os.getenv("APP_ENV", "dev"))
    configuration_directory: Path = Path(os.getenv("CONFIGURATION_DIR", ""))

    if not configuration_directory:
        exception = FileNotFoundError("No configuration file path provided")
        raise exception

    configuration_reader: ConfigurationReader = OmegaConfigurationReader(
        run_type_environment, configuration_directory
    )

    configuration_loader: Configuration = LoadConfiguration(configuration_reader, logger)
    configuration = configuration_loader.load()
    if not configuration:
        exception = ValueError("No configuration loaded")
        logger.critical(exception.__str__())
        raise ValueError("No configuration loaded")

    return configuration


def main() -> None:
    pprint(load_application_configuration())


if __name__ == "__main__":
    main()
