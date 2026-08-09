import uuid
from typing import Callable, Awaitable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from agentic_core.infrastructure.http.context.request_id_context import request_id_context


class RequestIDMiddleware(BaseHTTPMiddleware):
    REQUEST_TAG = "X-Request-ID"

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:

        request_id: str = request.headers.get(self.REQUEST_TAG) or self._generate_request_id()
        request_id_context.set(request_id)
        response: Response = await call_next(request)
        response.headers[self.REQUEST_TAG] = request_id

        return response

    @staticmethod
    def _generate_request_id() -> str:
        return uuid.uuid4().hex
