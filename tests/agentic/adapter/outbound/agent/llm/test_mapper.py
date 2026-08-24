from pydantic import SecretStr

from agentic.adapter.outbound.agent.llm.mapper import ModelSettingsMapper
from agentic_core.infrastructure.application_configuration.enum.connector_type import ConnectorType
from agentic_core.infrastructure.application_configuration.enum.http_method import HttpMethod
from agentic_core.infrastructure.application_configuration.model.connector import ApiConnector
from agentic_core.infrastructure.application_configuration.model.operation import ApiOperation
from agentic_core.infrastructure.authentication.model.auth_type import AuthType
from agentic_core.infrastructure.authentication.model.no_auth import NoAuth


def make_operation(parameters):
    connector = ApiConnector(
        name="conn",
        type=ConnectorType.api,
        auth=NoAuth(type=AuthType.none),
        base_url="http://example.com",
        timeout=10,
        retry=1,
    )
    return ApiOperation(
        name="gpt-model",
        connector=connector,
        endpoint="/chat",
        method=HttpMethod.POST,
        parameters=parameters,
    )


def test_maps_connector_base_url_and_hardcoded_api_key():
    mapper = ModelSettingsMapper(make_operation({}))

    connector, _ = mapper()

    assert connector.base_url == "http://example.com"
    assert isinstance(connector.api_key, SecretStr)
    assert connector.api_key.get_secret_value() == "No_Key"


def test_defaults_max_tokens_and_temperature_when_absent():
    mapper = ModelSettingsMapper(make_operation({}))

    _, parameters = mapper()

    assert parameters.model_name == "gpt-model"
    assert parameters.max_tokens == 8000
    assert parameters.temperature == 0.0


def test_uses_explicit_max_tokens_and_temperature_when_present():
    mapper = ModelSettingsMapper(make_operation({"max_tokens": 500, "temperature": 0.7}))

    _, parameters = mapper()

    assert parameters.max_tokens == 500
    assert parameters.temperature == 0.7
