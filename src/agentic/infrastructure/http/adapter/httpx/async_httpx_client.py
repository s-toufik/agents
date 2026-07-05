from typing import Optional, Any, Awaitable

from httpx import AsyncClient


class AsyncHttpxClient:

    def __init__(self, client: AsyncClient) -> None:
        self._client = client

    async def get(
        self,
        endpoint: str,
        *,
        params: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, Any]] = None,
    ) -> Awaitable[Any]:
        return self._client.get(endpoint, params=params, headers=headers)

    async def post(
        self,
        endpoint: str,
        *,
        body: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, Any]] = None,
    ) -> Awaitable[Any]:
        return self._client.post(endpoint, json=body, headers=headers)