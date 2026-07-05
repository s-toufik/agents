from functools import cached_property
from typing import Optional
from httpx import AsyncClient, Limits, Timeout, AsyncHTTPTransport

from agentic.infrastructure.http.adapter.httpx.async_httpx_client import AsyncHttpxClient
from agentic.infrastructure.http.port.async_http_client import AsyncHttpClient
from agentic.infrastructure.http.port.http_client_factory import HttpClientFactoryParams


class HttpxFactory:

    def __init__(self, factory_params: Optional[HttpClientFactoryParams] = None)  -> None:
        self._factory_params = factory_params or HttpClientFactoryParams()

    def create_async_http_client(self) -> AsyncHttpClient:
        instance = self.instance_async_http_client

        return AsyncHttpxClient(instance)

    @cached_property
    def instance_async_http_client(self) -> AsyncClient:
        limits = Limits(
            max_connections=self._factory_params.limits.max_connections,
            max_keepalive_connections=self._factory_params.limits.max_keep_alive_connections,
        )
        timeout = Timeout(self._factory_params.limits.timeout)
        transport = AsyncHTTPTransport(
            retries=self._factory_params.retry_policy.retry_count,
        )

        return AsyncClient(
            timeout=timeout,
            limits=limits,
            transport=transport
        )