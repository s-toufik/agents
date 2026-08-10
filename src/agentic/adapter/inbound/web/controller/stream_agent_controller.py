import asyncio
import json
from datetime import datetime
from typing import Callable, AsyncIterator

from starlette.responses import StreamingResponse

from agentic.adapter.inbound.web.schema.agent_message_schema import AgentMessageSchema
from agentic.adapter.inbound.web.schema.agent_message_stream_schema import AgentMessageStreamSchema
from agentic.adapter.inbound.web.schema.agent_request_schema import AgentRequestSchema
from agentic.application.port.inbound.stream_agent_port import StramAgentPort
from agentic.application.port.outbound.sse_queue_port import SSEQueuePort
from agentic.domain.enum.agent_message_status import MessageStreamType
from agentic.domain.model.agent_message_stream import AgentMessageStream
from agentic.domain.model.agent_request import AgentRequest
from agentic_core.infrastructure.http.context.request_id_context import request_id_context
from agentic_core.infrastructure.logger.port.logger import Logger


class StreamAgentController:
    def __init__(
        self,
        use_case: StramAgentPort,
        stream_events: Callable[[], SSEQueuePort],
        logger: Logger,
    ) -> None:
        self._use_case = use_case
        self._stream_events = stream_events
        self._logger = logger

    async def execute(self, request: AgentRequestSchema) -> StreamingResponse:

        request_id = request_id_context.get() or "N/A"
        self._logger.info(f"[{request_id}]: request received at {datetime.now()}")
        domain_request: AgentRequest = request.to_domain()
        events: SSEQueuePort = self._stream_events()

        asyncio.create_task(self._use_case.execute(domain_request, events))

        async def event_generator() -> AsyncIterator[bytes]:

            while True:
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

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )
