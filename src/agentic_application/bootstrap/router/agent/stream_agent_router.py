from fastapi import APIRouter, Body
from starlette.responses import StreamingResponse

from agentic.adapter.inbound.web.controller.stream_agent_controller import StreamAgentController
from agentic.adapter.inbound.web.schema.agent_request_schema import AgentRequestSchema


class StreamAgentRouter:
    PREFIX: str = "/api/v1"
    ENDPOINT: str = "/agent/stream"

    def __init__(self, controller: StreamAgentController) -> None:
        self._controller = controller
        self._router: APIRouter = APIRouter(prefix=self.PREFIX)
        self._router_registry()

    @property
    def router(self) -> APIRouter:
        return self._router

    def _router_registry(self) -> None:
        self._router.add_api_route(self.ENDPOINT, self._ask_agent, methods=["POST"])

    async def _ask_agent(self, request: AgentRequestSchema = Body(...)) -> StreamingResponse:
        return await self._controller.execute(request)
