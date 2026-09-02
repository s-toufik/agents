import json

from agentic.adapter.inbound.web.schema.agent_message_schema import AgentMessageSchema
from agentic.domain.enum.agent_message_status import MessageStreamType
from agentic.domain.enum.agent_message_type import AgentMessageType


def test_serialize_defaults():
    schema = AgentMessageSchema(session_id="s1", content="hello", metadata=None)

    serialized = schema.serialize()

    assert isinstance(serialized, bytes)
    text = serialized.decode("utf-8")

    # real SSE framing: exactly one `event:` line, one `data:` line, blank-line terminator
    event_line, data_line, blank = text.split("\n", 2)
    assert event_line == "event: final"
    assert blank == "\n"
    assert data_line.startswith("data: ")

    payload = json.loads(data_line.removeprefix("data: "))
    assert payload == {
        "session_id": "s1",
        "content": "hello",
        "metadata": None,
        "error": None,
        "message_status": "final",
        "message_type": "text",
    }


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
    event_line, data_line, _ = text.split("\n", 2)

    assert event_line == "event: error"
    payload = json.loads(data_line.removeprefix("data: "))
    assert payload["error"] == "boom"
    assert payload["message_status"] == "error"
    assert payload["message_type"] == "image"
    assert payload["metadata"] == {"k": "v"}


def test_serialize_preserves_multiline_content_without_breaking_framing():
    # This is the failure mode the JSON-encoded single `data:` line exists to prevent:
    # a raw multi-line traceback must not introduce extra, unterminated lines.
    traceback_text = 'Traceback (most recent call last):\n  File "x.py", line 1\nValueError: bad'
    schema = AgentMessageSchema(session_id="s3", content="", error=traceback_text, metadata=None)

    text = schema.serialize().decode("utf-8")

    assert text.endswith("\n\n")
    event_line, data_line, blank = text.split("\n", 2)
    assert blank == "\n"
    payload = json.loads(data_line.removeprefix("data: "))
    assert payload["error"] == traceback_text
