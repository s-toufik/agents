import asyncio
import json
from datetime import datetime
from typing import Callable, AsyncIterator

from starlette.responses import StreamingResponse

from agentic.adapter.inbound.web.schema.agent_request_schema import AgentRequestSchema
from agentic.application.port.inbound.stream_agent_port import StramAgentPort
from agentic.application.port.outbound.stream_events_port import StreamEventsPort
from agentic.domain.model.agent_request import AgentRequest
from agentic_core.infrastructure.http.context.request_id_context import request_id_context
from agentic_core.infrastructure.logger.port.logger import Logger


class StreamAgentController:
    def __init__(
        self,
        use_case: StramAgentPort,
        events_factory: Callable[[], StreamEventsPort],
        logger: Logger,
    ) -> None:
        self._use_case = use_case
        self._events_factory = events_factory
        self._logger = logger

    async def execute(self, request: AgentRequestSchema) -> StreamingResponse:

        request_id = request_id_context.get() or "N/A"
        self._logger.info(f"[{request_id}]: request received at {datetime.now()}")
        domain_request: AgentRequest = request.to_domain()
        events: StreamEventsPort = self._events_factory()

        asyncio.create_task(self._use_case.execute(domain_request, events))

        async def event_generator() -> AsyncIterator[str]:

            while True:
                event = await events.queue.get()

                if event["type"] == "complete":
                    yield ("event: done \ndata: {}\n\n")
                    break

                if event["type"] == "token":
                    yield (f"event: token \ndata: {json.dumps({'token': event['value']})}\n\n")

                elif event["type"] == "final":
                    yield (f"event: final \ndata: {json.dumps({'answer': event['value']})}\n\n")

                elif event["type"] == "error":
                    yield (f"event: error \ndata: {json.dumps({'message': event['value']})}\n\n")

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )
