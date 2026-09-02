from typing import cast

from pycraftcore.application_configuration.model.connector import ApiConnector
from pycraftcore.application_configuration.model.operation import ApiOperation

# from pycraftcore.authentication import NoAuth
from pydantic import SecretStr

from agentic.adapter.outbound.agent.llm.schema import ModelConnector, ModelParameters


class ModelSettingsMapper:
    def __init__(self, operation: ApiOperation) -> None:
        self._operation = operation

    def __call__(self) -> tuple[ModelConnector, ModelParameters]:
        connector: ApiConnector = self._operation.connector
        # auth : NoAuth = self._operation.connector.auth

        return (
            ModelConnector(
                base_url=connector.base_url,
                api_key=SecretStr("No_Key"),
            ),
            ModelParameters(
                model_name=self._operation.name,
                max_tokens=cast(int, self._operation.parameters.get("max_tokens", 8000)),
                temperature=cast(float, self._operation.parameters.get("temperature", 0.0)),
            ),
        )
