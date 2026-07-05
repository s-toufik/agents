from pydantic import BaseModel
from typing import Dict

from agentic.infrastructure.app_configuration.enum.connector_type import ConnectorType
from agentic.infrastructure.app_configuration.enum.run_type_application import (
    RunTypeApplication,
)
from agentic.infrastructure.app_configuration.enum.run_type_environment import (
    RunTypeEnvironment,
)
from agentic.infrastructure.app_configuration.model.configuration import AppConfiguration
from agentic.infrastructure.app_configuration.model.connector import ConnectorTyping

from agentic.infrastructure.app_configuration.model.operation import OperationTyping


class AppConfigurationSchema(BaseModel):
    env: RunTypeEnvironment
    run: RunTypeApplication
    connector: Dict[ConnectorType, Dict[str, ConnectorTyping]]
    operation: Dict[str, OperationTyping]


class MapperDomainSchema:
    @staticmethod
    def map(app_configuration_schema: AppConfigurationSchema) -> AppConfiguration:
        return AppConfiguration(**vars(app_configuration_schema))
