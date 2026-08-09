import os
import dotenv
from pathlib import Path
from pprint import pprint

from agentic_core.infrastructure.application_configuration.adapter.load_configuration import (
    LoadConfiguration,
)
from agentic_core.infrastructure.application_configuration.adapter import (
    OmegaConfigurationReader,
)
from agentic_core.infrastructure.application_configuration.enum.run_type_environment import (
    RunTypeEnvironment,
)
from agentic_core.infrastructure.application_configuration.model.configuration import (
    ApplicationConfiguration,
)
from agentic_core.infrastructure.application_configuration.port.configuration import Configuration
from agentic_core.infrastructure.application_configuration.port.configuration_reader import (
    ConfigurationReader,
)
from agentic_core.infrastructure.logger.adapter.loguru_logger import LoguruLogger
from agentic_core.infrastructure.logger import Logger

logger: Logger = LoguruLogger()


def load_application_configuration() -> ApplicationConfiguration:
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
