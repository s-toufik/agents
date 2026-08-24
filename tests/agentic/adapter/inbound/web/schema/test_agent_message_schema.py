from agentic.adapter.inbound.web.schema.agent_message_schema import AgentMessageSchema
from agentic.domain.enum.agent_message_status import MessageStreamType
from agentic.domain.enum.agent_message_type import AgentMessageType


def test_serialize_defaults():
    schema = AgentMessageSchema(session_id="s1", content="hello", metadata=None)

    serialized = schema.serialize()

    assert isinstance(serialized, bytes)
    text = serialized.decode("utf-8")
    assert "event_type: final\n" in text
    assert "session_id: s1\n" in text
    assert "content: hello\n" in text
    assert "metadata: None\n" in text
    assert "error: None\n" in text
    assert "message_status: final\n" in text
    assert "message_type: text\n" in text


def test_serialize_with_error_and_custom_status_type():
    schema = AgentMessageSchema(
        session_id="s2",
        content="",
        metadata={"k": "v"},
        error="boom",
        message_status=MessageStreamType.ERROR,
        message_type=AgentMessageType.IMAGE,
    )

    text = schema.serialize().decode("utf-8")

    assert "event_type: error\n" in text
    assert "error: boom\n" in text
    assert "message_status: error\n" in text
    assert "message_type: image\n" in text
    assert "metadata: {'k': 'v'}\n" in text
