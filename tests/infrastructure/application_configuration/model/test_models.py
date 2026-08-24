from agentic_core.infrastructure.application_configuration.enum.connector_type import ConnectorType
from agentic_core.infrastructure.application_configuration.enum.http_method import HttpMethod
from agentic_core.infrastructure.application_configuration.enum.run_type_application import (
    RunTypeApplication,
)
from agentic_core.infrastructure.application_configuration.enum.run_type_environment import (
    RunTypeEnvironment,
)
from agentic_core.infrastructure.application_configuration.model.configuration import (
    ApplicationConfiguration,
)
from agentic_core.infrastructure.application_configuration.model.connector import (
    ApiConnector,
    DatabaseConnector,
)
from agentic_core.infrastructure.application_configuration.model.operation import ApiOperation
from agentic_core.infrastructure.authentication.model.auth_type import AuthType
from agentic_core.infrastructure.authentication.model.no_auth import NoAuth


def test_application_configuration_holds_all_fields():
    config = ApplicationConfiguration(
        env=RunTypeEnvironment.develop,
        run=RunTypeApplication.synchronous,
        connector={},
        operation={},
    )

    assert config.env == RunTypeEnvironment.develop
    assert config.run == RunTypeApplication.synchronous


def test_api_connector_certificate_defaults_to_none():
    connector = ApiConnector(
        name="api",
        type=ConnectorType.api,
        auth=NoAuth(type=AuthType.none),
        base_url="http://x",
        timeout=1,
        retry=1,
    )

    assert connector.certificate is None


def test_database_connector_holds_pool_settings():
    connector = DatabaseConnector(
        name="db",
        type=ConnectorType.database,
        auth=NoAuth(type=AuthType.none),
        engine="sqlite",
        host="/tmp/db",
        port=0,
        default_name="main",
        pool={"min": 1, "max": 5},
    )

    assert connector.pool == {"min": 1, "max": 5}


def test_api_operation_holds_endpoint_method_and_parameters():
    connector = ApiConnector(
        name="api",
        type=ConnectorType.api,
        auth=NoAuth(type=AuthType.none),
        base_url="http://x",
        timeout=1,
        retry=1,
    )
    operation = ApiOperation(
        name="op",
        connector=connector,
        endpoint="/chat",
        method=HttpMethod.POST,
        parameters={"max_tokens": 100},
    )

    assert operation.endpoint == "/chat"
    assert operation.method == HttpMethod.POST
    assert operation.parameters == {"max_tokens": 100}
