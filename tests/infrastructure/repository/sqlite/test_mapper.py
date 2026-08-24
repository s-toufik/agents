from agentic_core.infrastructure.application_configuration.enum.connector_type import ConnectorType
from agentic_core.infrastructure.application_configuration.model.connector import DatabaseConnector
from agentic_core.infrastructure.authentication.model.auth_type import AuthType
from agentic_core.infrastructure.authentication.model.no_auth import NoAuth
from agentic_core.infrastructure.repository.sqlite.mapper import SqliteSettingsMapper


def test_maps_host_to_path_and_default_name():
    connector = DatabaseConnector(
        name="db",
        type=ConnectorType.database,
        auth=NoAuth(type=AuthType.none),
        engine="sqlite",
        host="/var/data",
        port=0,
        default_name="main",
        pool={},
    )
    mapper = SqliteSettingsMapper(connector)

    settings = mapper()

    assert settings.path == "/var/data"
    assert settings.default_name == "main"
