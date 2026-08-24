from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from agentic.adapter.outbound.agent.enum.role import Role
from agentic.adapter.outbound.agent.graph.schema.conversation import Conversation
from agentic.adapter.outbound.agent.graph.schema.conversation_message import ConversationMessage
from agentic.adapter.outbound.agent.graph.schema.tool_call import ToolCall


def make_message(role, content="hi", **kwargs):
    return ConversationMessage(role=role, content=content, **kwargs)


def test_last_and_last_assistant_on_empty_conversation():
    conversation = Conversation()

    assert conversation.last() is None
    assert conversation.first_user() is None
    assert conversation.last_assistant() is None


def test_last_returns_most_recently_appended_message():
    conversation = Conversation()
    conversation.append(make_message(Role.USER, "first"))
    conversation.append(make_message(Role.ASSISTANT, "second"))

    assert conversation.last().content == "second"


def test_first_user_finds_first_user_message_only():
    conversation = Conversation(
        [
            make_message(Role.SYSTEM, "sys"),
            make_message(Role.USER, "u1"),
            make_message(Role.USER, "u2"),
        ]
    )

    assert conversation.first_user().content == "u1"


def test_last_assistant_finds_most_recent_assistant_message():
    conversation = Conversation(
        [
            make_message(Role.ASSISTANT, "a1"),
            make_message(Role.USER, "u1"),
            make_message(Role.ASSISTANT, "a2"),
        ]
    )

    assert conversation.last_assistant().content == "a2"


def test_copy_produces_independent_message_list():
    original = Conversation([make_message(Role.USER, "u1")])
    copy = original.copy()
    copy.append(make_message(Role.ASSISTANT, "a1"))

    assert len(original.messages) == 1
    assert len(copy.messages) == 2


def test_to_langchain_maps_each_role_to_expected_message_type():
    conversation = Conversation(
        [
            make_message(Role.SYSTEM, "sys"),
            make_message(Role.USER, "user"),
            make_message(
                Role.ASSISTANT,
                "assistant",
                tool_calls=[ToolCall(id="call_1", name="tool_a", args={"x": 1})],
            ),
            make_message(Role.TOOL, "tool-result", tool_call_id="call_1"),
        ]
    )

    lc_messages = conversation.to_langchain()

    assert isinstance(lc_messages[0], SystemMessage)
    assert isinstance(lc_messages[1], HumanMessage)
    assert isinstance(lc_messages[2], AIMessage)
    assert len(lc_messages[2].tool_calls) == 1
    assert lc_messages[2].tool_calls[0]["id"] == "call_1"
    assert lc_messages[2].tool_calls[0]["name"] == "tool_a"
    assert lc_messages[2].tool_calls[0]["args"] == {"x": 1}
    assert isinstance(lc_messages[3], ToolMessage)
    assert lc_messages[3].tool_call_id == "call_1"


def test_from_langchain_round_trips_back_to_conversation_messages():
    lc_messages = [
        SystemMessage(content="sys"),
        HumanMessage(content="user"),
        AIMessage(
            content="assistant",
            tool_calls=[{"id": "call_1", "name": "tool_a", "args": {"x": 1}}],
        ),
        ToolMessage(content="tool-result", tool_call_id="call_1"),
    ]

    conversation = Conversation.from_langchain(lc_messages)

    assert [m.role for m in conversation.messages] == [
        Role.SYSTEM,
        Role.USER,
        Role.ASSISTANT,
        Role.TOOL,
    ]
    assert conversation.messages[2].tool_calls == [
        ToolCall(id="call_1", name="tool_a", args={"x": 1})
    ]
    assert conversation.messages[3].tool_call_id == "call_1"


def test_to_langchain_then_from_langchain_is_a_full_round_trip():
    original = Conversation(
        [
            make_message(Role.USER, "user"),
            make_message(
                Role.ASSISTANT,
                "assistant",
                tool_calls=[ToolCall(id="call_1", name="tool_a", args={})],
            ),
        ]
    )

    round_tripped = Conversation.from_langchain(original.to_langchain())

    assert [m.role for m in round_tripped.messages] == [Role.USER, Role.ASSISTANT]
    assert round_tripped.messages[1].tool_calls == original.messages[1].tool_calls
