from typing import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from agentic_core.infrastructure.http.context.request_id_context import request_context


class RequestMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        token = request_context.set(request)
        try:
            response = await call_next(request)
        finally:
            request_context.reset(token)

        return response
