import pytest

from agentic.adapter.inbound.web.schema.agent_message_stream_schema import (
    AgentMessageStreamSchema,
)
from agentic.domain.enum.agent_message_status import MessageStreamType


@pytest.mark.parametrize("stream_type", list(MessageStreamType))
def test_serialize_for_every_stream_type(stream_type):
    schema = AgentMessageStreamSchema(type=stream_type, content="payload")

    text = schema.serialize().decode("utf-8")

    assert text == f"event_type: {stream_type.value}\ncontent: payload\n"
