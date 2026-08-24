from dataclasses import dataclass

from agentic.adapter.outbound.agent.service.tokens_service import (
    _count_tokens,
    count_message_tokens,
)


def test_count_tokens_empty_string_is_zero():
    assert _count_tokens("") == 0


def test_count_tokens_counts_words_and_punctuation():
    # "hello, world!" -> 2 words, each with one run of punctuation attached
    assert _count_tokens("hello, world!") == 4


def test_count_tokens_plain_words_have_no_punctuation_bonus():
    assert _count_tokens("hello world") == 2


@dataclass
class FakeMessage:
    content: object


def test_count_message_tokens_adds_four_overhead_per_message():
    messages = [FakeMessage(content="hello world")]

    assert count_message_tokens(messages) == 2 + 4


def test_count_message_tokens_coerces_non_str_content():
    messages = [FakeMessage(content=12345)]

    assert count_message_tokens(messages) == _count_tokens("12345") + 4


def test_count_message_tokens_sums_across_messages():
    messages = [FakeMessage(content="a"), FakeMessage(content="b c")]

    assert count_message_tokens(messages) == (1 + 4) + (2 + 4)
