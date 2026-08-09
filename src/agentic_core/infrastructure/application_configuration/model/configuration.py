from typing import Dict
from dataclasses import dataclass

from agentic_core.infrastructure.application_configuration.enum.connector_type import ConnectorType
from agentic_core.infrastructure.application_configuration.enum.run_type_application import (
    RunTypeApplication,
)
from agentic_core.infrastructure.application_configuration.enum.run_type_environment import (
    RunTypeEnvironment,
)
from agentic_core.infrastructure.application_configuration.model.connector import ConnectorTyping
from agentic_core.infrastructure.application_configuration.model.operation import OperationTyping


@dataclass(frozen=True, slots=True)
class ApplicationConfiguration:
    env: RunTypeEnvironment
    run: RunTypeApplication
    connector: Dict[ConnectorType, Dict[str, ConnectorTyping]]
    operation: Dict[str, OperationTyping]
