import asyncio

from agentic.domain.enum.agent_message_status import MessageStreamType
from agentic.domain.model.agent_message_stream import AgentMessageStream


class SSEQueue:
    def __init__(self):
        self.queue: asyncio.Queue[AgentMessageStream] = asyncio.Queue()

    async def token(self, value: str) -> None:
        await self.queue.put(AgentMessageStream(type=MessageStreamType.TOKEN, content=value))

    async def final(self, value: str, metadata: dict[str, str] | None = None) -> None:
        await self.queue.put(
            AgentMessageStream(type=MessageStreamType.FINAL, content=value, metadata=metadata)
        )

    async def error(self, value: str) -> None:
        await self.queue.put(AgentMessageStream(type=MessageStreamType.ERROR, content=value))

    async def complete(self) -> None:
        await self.queue.put(AgentMessageStream(type=MessageStreamType.COMPLETE, content=""))
