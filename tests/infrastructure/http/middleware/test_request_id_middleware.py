import pytest
from unittest.mock import AsyncMock, MagicMock

from agentic_core.infrastructure.http.middleware.request_id_middleware import RequestIDMiddleware


def make_middleware():
    return RequestIDMiddleware(app=MagicMock())


@pytest.mark.asyncio
async def test_reuses_existing_request_id_header():
    middleware = make_middleware()
    request = MagicMock()
    request.headers = {"X-Request-ID": "existing-id"}
    response = MagicMock()
    response.headers = {}
    call_next = AsyncMock(return_value=response)

    result = await middleware.dispatch(request, call_next)

    assert result.headers["X-Request-ID"] == "existing-id"


@pytest.mark.asyncio
async def test_generates_request_id_when_header_absent():
    middleware = make_middleware()
    request = MagicMock()
    request.headers = {}
    response = MagicMock()
    response.headers = {}
    call_next = AsyncMock(return_value=response)

    result = await middleware.dispatch(request, call_next)

    assert "X-Request-ID" in result.headers
    assert len(result.headers["X-Request-ID"]) == 32
