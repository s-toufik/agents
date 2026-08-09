from dataclasses import dataclass, field
from typing import Protocol

from agentic_core.infrastructure.http.port.async_http_client import AsyncHttpClient


@dataclass(slots=True, frozen=True)
class RetryPolicy:
    retry_count: int = 3
    retry_delay: int = 1
    retry_backoff: int = 2
    retry_on_status_codes: list[int] = field(default_factory=list)


@dataclass(slots=True, frozen=True)
class Limits:
    timeout: int = 30
    max_connections: int = 100
    max_keep_alive_connections: int = 50


@dataclass(slots=True, frozen=True)
class ClientParams:
    base_url: str = ""


@dataclass(slots=True)
class HttpClientFactoryParams:
    client_params: ClientParams = field(default_factory=ClientParams)
    limits: Limits = field(default_factory=Limits)
    retry_policy: RetryPolicy = field(default_factory=RetryPolicy)


class HttpClientFactory(Protocol):
    def create_async_http_client(self) -> AsyncHttpClient: ...
