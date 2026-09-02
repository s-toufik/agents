import json

import pytest

from agentic.adapter.inbound.web.schema.agent_message_stream_schema import (
    AgentMessageStreamSchema,
)
from agentic.domain.enum.agent_message_status import MessageStreamType


@pytest.mark.parametrize("stream_type", list(MessageStreamType))
def test_serialize_for_every_stream_type(stream_type):
    schema = AgentMessageStreamSchema(type=stream_type, content="payload")

    text = schema.serialize().decode("utf-8")

    assert text == f'event: {stream_type.value}\ndata: {{"type":"{stream_type.value}","content":"payload"}}\n\n'


def test_serialize_preserves_multiline_content_without_breaking_framing():
    schema = AgentMessageStreamSchema(type=MessageStreamType.TOKEN, content="line one\nline two")

    text = schema.serialize().decode("utf-8")

    assert text.endswith("\n\n")
    event_line, data_line, blank = text.split("\n", 2)
    assert event_line == "event: token"
    assert blank == "\n"
    assert json.loads(data_line.removeprefix("data: ")) == {
        "type": "token",
        "content": "line one\nline two",
    }
