from dataclasses import dataclass, field
from typing import Dict, Union

from agentic_core.infrastructure.application_configuration.enum.connector_type import ConnectorType
from agentic_core.infrastructure.authentication import AuthTyping


@dataclass(slots=True)
class BaseConnector:
    name: str
    type: ConnectorType
    auth: AuthTyping


@dataclass(slots=True)
class ApiConnector(BaseConnector):
    base_url: str
    timeout: int
    retry: int
    certificate: str = field(default=None)


@dataclass(slots=True)
class DatabaseConnector(BaseConnector):
    engine: str
    host: str
    port: int
    default_name: str
    pool: Dict[str, int]


@dataclass(slots=True)
class FileConnector(BaseConnector):
    base_path: str


@dataclass(slots=True)
class TelemetryConnector(BaseConnector):
    host: str
    port: int


ConnectorTyping = Union[ApiConnector, FileConnector, DatabaseConnector, TelemetryConnector]
