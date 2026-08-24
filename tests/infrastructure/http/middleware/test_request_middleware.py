import pytest
from unittest.mock import MagicMock

from agentic_core.infrastructure.http.context.request_id_context import request_context
from agentic_core.infrastructure.http.middleware.request_middleware import RequestMiddleware


def make_middleware():
    return RequestMiddleware(app=MagicMock())


@pytest.mark.asyncio
async def test_sets_request_in_context_during_call_next():
    middleware = make_middleware()
    request = MagicMock()
    seen_context_request = {}

    async def call_next(_request):
        seen_context_request["value"] = request_context.get()
        return MagicMock()

    await middleware.dispatch(request, call_next)

    assert seen_context_request["value"] is request


@pytest.mark.asyncio
async def test_context_reset_even_when_call_next_raises():
    middleware = make_middleware()
    request = MagicMock()

    async def call_next(_request):
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        await middleware.dispatch(request, call_next)

    assert request_context.get() is None
