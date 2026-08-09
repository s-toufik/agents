from httpx import AsyncClient
from langchain_openai import ChatOpenAI

from agentic.adapter.outbound.agent.llm.schema import ModelConnector, ModelParameters


class LLMChat:
    def __init__(
        self,
        model_connector: ModelConnector,
        model_parameters: ModelParameters,
        async_client_httpx: AsyncClient | None = None,
    ) -> None:
        self._model_connector = model_connector
        self._model_parameters = model_parameters
        self._async_client_httpx = async_client_httpx

    def create_chat_client(self, streaming: bool = False) -> ChatOpenAI:
        return ChatOpenAI(
            base_url=self._model_connector.base_url,
            api_key=self._model_connector.api_key,
            model=self._model_parameters.model_name,
            http_async_client=self._async_client_httpx,
            max_tokens=self._model_parameters.max_tokens,
            temperature=self._model_parameters.temperature,
            streaming=streaming,
        )
