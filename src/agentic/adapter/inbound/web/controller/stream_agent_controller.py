import asyncio
import traceback
from asyncio import Task
from datetime import datetime
from typing import Callable, AsyncIterator

from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import StreamingResponse

from agentic.adapter.inbound.web.schema.agent_message_schema import AgentMessageSchema
from agentic.adapter.inbound.web.schema.agent_message_stream_schema import AgentMessageStreamSchema
from agentic.adapter.inbound.web.schema.agent_request_schema import AgentRequestSchema
from agentic.application.port.inbound.stream_agent_port import StramAgentPort
from agentic.application.port.outbound.sse_queue_port import SSEQueuePort
from agentic.domain.enum.agent_message_status import MessageStreamType
from agentic.domain.model.agent_message_stream import AgentMessageStream
from agentic.domain.model.agent_request import AgentRequest
from agentic_core.infrastructure.http.context.request_id_context import (
    request_id_context,
    request_context,
)
from agentic_core.infrastructure.logger.port.logger import Logger


class StreamAgentController:
    def __init__(
        self,
        use_case: StramAgentPort,
        stream_events: Callable[[], SSEQueuePort],
        logger: Logger,
        max_concurrent_streams: int = 200,
    ) -> None:
        self._use_case = use_case
        self._stream_events = stream_events
        self._logger = logger
        self._admission = asyncio.Semaphore(max_concurrent_streams)

    async def execute(self, request: AgentRequestSchema) -> StreamingResponse:

        request_id = request.request_id or request_id_context.get() or "N/A"

        if self._admission.locked():
            self._logger.warning(f"[{request_id}] rejected: server at capacity")
            raise HTTPException(status_code=503, detail="Server is at capacity, please retry.")

        await self._admission.acquire()

        try:
            starlette_request: Request | None = request_context.get() or None
            self._logger.info(f"[{request_id}]: request received at {datetime.now()}")

            domain_request: AgentRequest = request.to_domain()
            events: SSEQueuePort = self._stream_events()

            use_case_task: Task[None] = asyncio.create_task(
                self._use_case.execute(domain_request, events)
            )
        except Exception:
            self._admission.release()
            raise

        async def event_generator() -> AsyncIterator[bytes]:
            try:
                while True:
                    if starlette_request and await starlette_request.is_disconnected():
                        raise asyncio.CancelledError

                    event: AgentMessageStream = await events.queue.get()

                    if event.type != MessageStreamType.FINAL:
                        schema = AgentMessageStreamSchema(
                            type=event.type,
                            content=event.content or "",
                        )
                        yield schema.serialize()

                    elif event.type == MessageStreamType.FINAL:
                        yield AgentMessageSchema(
                            session_id=request.request_id,
                            content=event.content or "",
                            metadata=event.metadata,
                        ).serialize()

                    if event.type == MessageStreamType.COMPLETE:
                        break

            except asyncio.CancelledError:
                self._logger.warning(f"[{request_id}] request was canceled by user")
                raise
            except Exception as exception:
                traceback_str: str = "".join(traceback.format_exception(exception))
                self._logger.error(f"[{request_id}] Unhandled error:\n{traceback_str}")
                yield AgentMessageSchema(
                    session_id=request.request_id, content="", error=traceback_str, metadata={}
                ).serialize()
                raise
            finally:
                if not use_case_task.done():
                    use_case_task.cancel()
                    try:
                        await use_case_task
                    except BaseException:
                        pass
                self._admission.release()

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )
