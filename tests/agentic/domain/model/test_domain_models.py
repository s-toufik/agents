from agentic.domain.model.agent_message import AgentMessage
from agentic.domain.model.agent_message_stream import AgentMessageStream
from agentic.domain.model.agent_request import AgentRequest
from agentic.domain.enum.agent_message_status import MessageStreamType
from agentic.domain.enum.agent_message_type import AgentMessageType


def test_agent_message_defaults():
    message = AgentMessage(session_id="s1", content="hello", metadata=None)

    assert message.message_status == MessageStreamType.FINAL
    assert message.message_type == AgentMessageType.TEXT
    assert message.error is None


def test_agent_message_explicit_values():
    message = AgentMessage(
        session_id="s1",
        content="hello",
        metadata={"a": "b"},
        error="boom",
        message_status=MessageStreamType.ERROR,
        message_type=AgentMessageType.IMAGE,
    )

    assert message.metadata == {"a": "b"}
    assert message.error == "boom"
    assert message.message_status == MessageStreamType.ERROR
    assert message.message_type == AgentMessageType.IMAGE


def test_agent_message_stream_default_metadata_is_none():
    stream = AgentMessageStream(type=MessageStreamType.TOKEN, content="tok")

    assert stream.metadata is None


def test_agent_message_stream_explicit_metadata():
    stream = AgentMessageStream(
        type=MessageStreamType.FINAL, content="done", metadata={"iteration": 3}
    )

    assert stream.metadata == {"iteration": 3}


def test_agent_request_fields():
    request = AgentRequest(message="hi", model_name="gpt", request_id="req-1")

    assert request.message == "hi"
    assert request.model_name == "gpt"
    assert request.request_id == "req-1"
