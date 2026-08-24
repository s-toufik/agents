import pytest

from agentic.adapter.outbound.agent.streaming.sse_queue import SSEQueue
from agentic.domain.enum.agent_message_status import MessageStreamType


@pytest.mark.asyncio
async def test_token_puts_token_event_on_queue():
    queue = SSEQueue()

    await queue.token("hi")

    event = queue.queue.get_nowait()
    assert event.type == MessageStreamType.TOKEN
    assert event.content == "hi"


@pytest.mark.asyncio
async def test_final_puts_final_event_with_optional_metadata():
    queue = SSEQueue()

    await queue.final("done", metadata={"iteration": "3"})

    event = queue.queue.get_nowait()
    assert event.type == MessageStreamType.FINAL
    assert event.content == "done"
    assert event.metadata == {"iteration": "3"}


@pytest.mark.asyncio
async def test_final_without_metadata_defaults_to_none():
    queue = SSEQueue()

    await queue.final("done")

    event = queue.queue.get_nowait()
    assert event.metadata is None


@pytest.mark.asyncio
async def test_error_puts_error_event_on_queue():
    queue = SSEQueue()

    await queue.error("boom")

    event = queue.queue.get_nowait()
    assert event.type == MessageStreamType.ERROR
    assert event.content == "boom"


@pytest.mark.asyncio
async def test_complete_puts_complete_event_with_empty_content():
    queue = SSEQueue()

    await queue.complete()

    event = queue.queue.get_nowait()
    assert event.type == MessageStreamType.COMPLETE
    assert event.content == ""
