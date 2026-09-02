import asyncio

import pytest
from starlette.exceptions import HTTPException

from starlette.responses import StreamingResponse

from agentic.adapter.inbound.web.controller.stream_agent_controller import StreamAgentController
from agentic.adapter.inbound.web.schema.agent_request_schema import AgentRequestSchema
from agentic.adapter.outbound.agent.streaming.sse_queue import SSEQueue


def make_request(request_id: str = "req_1") -> AgentRequestSchema:
    return AgentRequestSchema(message="hi", model_name="gpt-oss-20b", request_id=request_id)


async def drain(response: StreamingResponse) -> None:
    async for _ in response.body_iterator:
        pass


class ImmediateCompleteUseCase:
    """Puts COMPLETE on the queue right away so the stream finishes fast."""

    async def execute(self, request, events) -> None:
        await events.complete()


class HangingUseCase:
    """Never completes on its own; relies on cancellation to end the stream."""

    async def execute(self, request, events) -> None:
        await asyncio.sleep(3600)


@pytest.mark.asyncio
async def test_execute_rejects_with_503_when_at_capacity():
    controller = StreamAgentController(
        HangingUseCase(), SSEQueue, logger=_NullLogger(), max_concurrent_streams=1
    )

    response = await controller.execute(make_request("req_1"))
    assert isinstance(response, StreamingResponse)

    with pytest.raises(HTTPException) as exc_info:
        await controller.execute(make_request("req_2"))

    assert exc_info.value.status_code == 503

    drain_task = asyncio.create_task(drain(response))
    await asyncio.sleep(0)
    drain_task.cancel()
    try:
        await drain_task
    except asyncio.CancelledError, GeneratorExit:
        pass


@pytest.mark.asyncio
async def test_execute_releases_admission_slot_after_stream_completes():
    controller = StreamAgentController(
        ImmediateCompleteUseCase(), SSEQueue, logger=_NullLogger(), max_concurrent_streams=1
    )

    first_response = await controller.execute(make_request("req_1"))
    await drain(first_response)

    second_response = await controller.execute(make_request("req_2"))
    assert isinstance(second_response, StreamingResponse)
    await drain(second_response)


class _NullLogger:
    def info(self, *_args, **_kwargs) -> None: ...
    def warning(self, *_args, **_kwargs) -> None: ...
    def error(self, *_args, **_kwargs) -> None: ...
