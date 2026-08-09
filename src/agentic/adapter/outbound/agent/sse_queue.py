import asyncio


class SSEQueue:
    def __init__(self):
        self.queue: asyncio.Queue = asyncio.Queue()

    async def token(self, value: str) -> None:
        await self.queue.put({"type": "token", "value": value})

    async def final(self, value: str) -> None:
        await self.queue.put({"type": "final", "value": value})

    async def error(self, value: str) -> None:
        await self.queue.put({"type": "error", "value": value})

    async def complete(self) -> None:
        await self.queue.put({"type": "complete"})
