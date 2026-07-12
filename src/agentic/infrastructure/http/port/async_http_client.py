from typing import Protocol, Optional, Any


class AsyncHttpClient(Protocol):
    async def get(
        self,
        endpoint: str,
        *,
        params: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, Any]] = None,
    ) -> Any: ...
    async def post(
        self,
        endpoint: str,
        *,
        body: Optional[dict[str, Any]] = None,
        headers: Optional[dict[str, Any]] = None,
    ) -> Any: ...
