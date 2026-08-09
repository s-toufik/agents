import ssl
from datetime import timedelta
from functools import cached_property
from typing import Any, Awaitable, Callable, Mapping, Optional

import orjson
from aiobreaker import CircuitBreaker, CircuitBreakerListener
from httpx import (
    AsyncBaseTransport,
    AsyncClient,
    AsyncHTTPTransport,
    Limits,
    Request,
    Response,
    Timeout,
)
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from agentic_core.infrastructure.application_configuration.enum.http_method import HttpMethod
from agentic_core.infrastructure.http.configuration.http_client_configuration import (
    HttpClientSettings,
)
from agentic_core.infrastructure.http.port.async_http_client import AsyncHttpClient
from agentic_core.infrastructure.logger.port.logger import Logger


class HttpxClientFactory:
    def __init__(
        self,
        http_client_settings: Optional[HttpClientSettings] = None,
        logger: Optional[Logger] = None,
        http_transport: Optional[AsyncHTTPTransport] = None,
    ) -> None:
        self._http_client_settings: HttpClientSettings = (
            http_client_settings or HttpClientSettings()
        )
        self._logger = logger
        self._owns_client: bool = True
        self._http_transport = http_transport

    async def __aenter__(self) -> "HttpxClientFactory":
        _ = self._client_instance
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def start(self) -> None:
        pass

    async def close(self) -> None:
        if self._owns_client and not self._client_instance.is_closed:
            await self._client_instance.aclose()

    def create_client(self) -> AsyncHttpClient:
        return HttpxClient(self._client_instance)

    @cached_property
    def _client_instance(self) -> AsyncClient:
        limits = Limits(
            max_connections=self._http_client_settings.limits.max_connections,
            max_keepalive_connections=(
                self._http_client_settings.limits.max_keep_alive_connections
            ),
            keepalive_expiry=(self._http_client_settings.limits.keep_alive_timeout),
        )

        timeout = Timeout(self._http_client_settings.limits.timeout)

        if not self._http_transport:
            self._http_transport = AsyncHTTPTransport(
                retries=self._http_client_settings.retry.retry_count,
                verify=self._create_ssl_from_certificate(),
            )

        hooks = {"request": [self._event_log]} if self._event() else None

        client = AsyncClient(
            base_url=(self._http_client_settings.client_params.base_url or ""),
            timeout=timeout,
            limits=limits,
            transport=self._http_transport,
            event_hooks=hooks,
        )

        return client

    @property
    def resilient_client_instance(self) -> AsyncClient:
        return self._resilient_client_instance

    @cached_property
    def _resilient_client_instance(self) -> AsyncClient:
        limits = Limits(
            max_connections=self._http_client_settings.limits.max_connections,
            max_keepalive_connections=(
                self._http_client_settings.limits.max_keep_alive_connections
            ),
            keepalive_expiry=(self._http_client_settings.limits.keep_alive_timeout),
        )

        timeout = Timeout(self._http_client_settings.limits.timeout)

        if not self._http_transport:
            self._http_transport = AsyncHTTPTransport(
                verify=self._create_ssl_from_certificate(),
            )

        client = AsyncClient(
            base_url=(self._http_client_settings.client_params.base_url or ""),
            timeout=timeout,
            limits=limits,
            transport=ResilientTransport(
                http_client_settings=self._http_client_settings,
                logger=self._logger,
                transport=self._http_transport,
            ),
        )

        return client

    def _create_ssl_from_certificate(self) -> bool | str | ssl.SSLContext:
        cert_path = self._http_client_settings.security.certificate

        if cert_path:
            ctx = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)
            ctx.load_verify_locations(cafile=cert_path)
            return ctx

        return False

    def _event(
        self,
    ) -> list[Callable[[Request], Awaitable[Any]]]:
        return [self._event_log]

    async def _event_log(self, request: Request) -> None:
        counter: int = 0

        if self._logger:
            self._logger.info(
                f"Executing request {request.method} -> {request.url} -- Attempt #{counter}"
            )


class HttpxClient:
    __slots__ = ("_client",)

    def __init__(self, client: AsyncClient) -> None:
        self._client = client

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Mapping[str, Any]] = None,
        json: Optional[Mapping[str, Any]] = None,
        headers: Optional[Mapping[str, str]] = None,
    ) -> Any:
        response = await self._client.request(
            method=method,
            url=endpoint,
            params=params,
            json=json,
            headers=headers,
        )

        response.raise_for_status()

        if "application/json" in response.headers.get("Content-Type", ""):
            return orjson.loads(response.content)

        return response.text

    async def get(
        self,
        endpoint: str,
        params: Optional[Mapping[str, Any]] = None,
        headers: Optional[Mapping[str, str]] = None,
    ) -> Any:
        return await self._request(
            HttpMethod.GET.value,
            endpoint,
            params=params,
            headers=headers,
        )

    async def post(
        self,
        endpoint: str,
        body: Optional[Mapping[str, Any]] = None,
        headers: Optional[Mapping[str, str]] = None,
    ) -> Any:
        return await self._request(
            HttpMethod.POST.value,
            endpoint,
            json=body,
            headers=headers,
        )


class BreakerLogger(CircuitBreakerListener):
    def __init__(self, logger: Optional[Logger] = None):
        self._logger = logger
        self._last_exc = None

    def failure(self, cb, exc):
        self._last_exc = exc

        if self._logger:
            self._logger.warning(
                f"[breaker] failure ({cb.fail_counter}/{cb.fail_max}) recorded: {exc!r}"
            )

    def success(self, cb):
        self._last_exc = None

    def state_change(self, cb, old_state, new_state):
        if self._logger:
            self._logger.info(f"[breaker] {old_state.state} -> {new_state.state}")

        if type(new_state).__name__ == "CircuitOpenState":
            if self._logger:
                self._logger.error(
                    f"[breaker] OPEN - "
                    f"{cb.fail_counter} consecutive failures reached "
                    f"fail_max={cb.fail_max}. "
                    f"Last error: {self._last_exc!r}. "
                    f"Will allow a trial call again after "
                    f"{cb.timeout_duration}."
                )


class ResilientTransport(AsyncBaseTransport):
    def __init__(
        self,
        http_client_settings: Optional[HttpClientSettings] = None,
        logger: Optional[Logger] = None,
        transport: Optional[AsyncBaseTransport] = None,
    ):
        self._http_client_settings: HttpClientSettings = (
            http_client_settings or HttpClientSettings()
        )
        self._logger = logger
        self._transport = transport or AsyncHTTPTransport()

        self._breaker_logger = BreakerLogger(logger)

        self._breaker = CircuitBreaker(
            fail_max=(self._http_client_settings.circuit_breaker.failure_threshold),
            timeout_duration=timedelta(
                seconds=(self._http_client_settings.circuit_breaker.recovery_timeout)
            ),
            listeners=[self._breaker_logger],
        )

        self._retryer = AsyncRetrying(
            retry=retry_if_exception_type(self._http_client_settings.retry.retry_on),
            stop=stop_after_attempt(self._http_client_settings.retry.retry_count),
            wait=wait_exponential(
                multiplier=self._http_client_settings.retry.retry_delay,
                min=2,
                max=60,
            ),
            reraise=True,
            before_sleep=self._log_retry,
        )

    def _log_retry(self, retry_state) -> None:
        exc = retry_state.outcome.exception()

        if self._logger:
            self._logger.warning(
                f"[retry] attempt "
                f"{retry_state.attempt_number} failed: "
                f"{exc!r}; retrying in "
                f"{retry_state.next_action.sleep:.1f}s"
            )

    async def _retry_execute(self, request: Request) -> Response:
        return await self._retryer(
            self._transport.handle_async_request,
            request,
        )

    async def handle_async_request(
        self,
        request: Request,
    ) -> Response:
        return await self._breaker.call_async(
            self._retry_execute,
            request,
        )

    async def aclose(self) -> None:
        await self._transport.aclose()
