from typing import Dict
from dataclasses import dataclass

from agentic.infrastructure.app_configuration.enum.connector_type import ConnectorType
from agentic.infrastructure.app_configuration.enum.run_type_application import (
    RunTypeApplication,
)
from agentic.infrastructure.app_configuration.enum.run_type_environment import (
    RunTypeEnvironment,
)
from agentic.infrastructure.app_configuration.model.connector import ConnectorTyping
from agentic.infrastructure.app_configuration.model.operation import OperationTyping


@dataclass(frozen=True, slots=True)
class AppConfiguration:
    env: RunTypeEnvironment
    run: RunTypeApplication
    connector: Dict[ConnectorType, Dict[str, ConnectorTyping]]
    operation: Dict[str, OperationTyping]
