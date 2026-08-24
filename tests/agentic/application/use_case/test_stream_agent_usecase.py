import pytest
from unittest.mock import AsyncMock, MagicMock

from agentic.application.use_case.stream_agent_usecase import StreamAgentUseCase, on_token
from agentic.domain.model.agent_message import AgentMessage
from agentic.domain.model.agent_request import AgentRequest


def make_request():
    return AgentRequest(message="hi", model_name="gpt", request_id="s1")


@pytest.mark.asyncio
async def test_success_path_pushes_final_then_complete():
    agent = MagicMock()
    agent.run = AsyncMock(
        return_value=AgentMessage(session_id="s1", content="answer", metadata={"k": "v"})
    )
    events = MagicMock()
    events.final = AsyncMock()
    events.complete = AsyncMock()
    events.error = AsyncMock()
    use_case = StreamAgentUseCase(agent, logger=MagicMock())

    await use_case.execute(make_request(), events)

    events.final.assert_awaited_once_with("answer", metadata={"k": "v"})
    events.complete.assert_awaited_once()
    events.error.assert_not_called()


@pytest.mark.asyncio
async def test_agent_failure_pushes_error_then_still_completes():
    agent = MagicMock()
    agent.run = AsyncMock(side_effect=RuntimeError("boom"))
    events = MagicMock()
    events.final = AsyncMock()
    events.complete = AsyncMock()
    events.error = AsyncMock()
    use_case = StreamAgentUseCase(agent, logger=MagicMock())

    await use_case.execute(make_request(), events)

    events.final.assert_not_called()
    events.error.assert_awaited_once()
    assert "boom" in events.error.call_args[0][0]
    events.complete.assert_awaited_once()


@pytest.mark.asyncio
async def test_on_token_is_a_no_op_when_no_context_var_set():
    # No StreamAgentUseCase.execute is running, so the context var is unset.
    await on_token("should not raise")
