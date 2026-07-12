import re


def _count_tokens(text: str) -> int:
    if not text:
        return 0
    return sum(1 + len(re.findall(r"[^a-zA-Z0-9]+", word)) for word in text.split())


def count_message_tokens(messages: list) -> int:
    return sum(
        _count_tokens(msg.content if isinstance(msg.content, str) else str(msg.content)) + 4
        for msg in messages
    )
