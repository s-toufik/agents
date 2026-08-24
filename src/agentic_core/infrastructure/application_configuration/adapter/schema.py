from pydantic import BaseModel
from typing import Dict


from agentic_core.infrastructure.application_configuration.enum.connector_type import ConnectorType
from agentic_core.infrastructure.application_configuration.enum.run_type_application import (
    RunTypeApplication,
)
from agentic_core.infrastructure.application_configuration.enum.run_type_environment import (
    RunTypeEnvironment,
)
from agentic_core.infrastructure.application_configuration.model.configuration import (
    ApplicationConfiguration,
)
from agentic_core.infrastructure.application_configuration.model.connector import ConnectorTyping

from agentic_core.infrastructure.application_configuration.model.operation import OperationTyping


class ApplicationConfigurationSchema(BaseModel):
    env: RunTypeEnvironment
    run: RunTypeApplication
    connector: Dict[ConnectorType, Dict[str, ConnectorTyping]]
    operation: Dict[str, OperationTyping]


class MapperDomainSchema:
    @staticmethod
    def map(app_configuration_schema: ApplicationConfigurationSchema) -> ApplicationConfiguration:
        return ApplicationConfiguration(**vars(app_configuration_schema))
