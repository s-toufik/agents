import traceback
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI, APIRouter
from pycraftcore.http.middleware import RequestMiddleware
from pycraftcore.http.middleware.request_id_middleware import RequestIDMiddleware
from starlette.middleware.cors import CORSMiddleware

from agentic_application.bootstrap.container.agent.agent_container import AgentContainer


@asynccontextmanager
async def _lifespan(application: FastAPI, container: AgentContainer) -> AsyncGenerator[None]:
    status: bool
    boot_exception: Exception | None

    # Must wrap everything else: tool discovery during boot happens over an
    # in-process MCP session connected to this server, so its session manager has
    # to be live before boot runs.
    async with container.mcp_lifespan():
        status, boot_exception = await container.boot
        container.logging.info("Container booted")
        if not status and boot_exception:
            container.logging.error(f"Container failed to boot: {boot_exception}")
            traceback_str: str = "".join(traceback.format_exception(boot_exception))
            container.logging.error(traceback_str)
            raise RuntimeError("Container failed to boot") from boot_exception

        try:
            routers: list[APIRouter] = await container.create_routers
            try:
                for router in routers:
                    application.include_router(router)
                    container.logging.info(f"Router {router.prefix} included")
            except Exception as exception:
                container.logging.error(f"Error including router: {exception}")
                traceback_str: str = "".join(traceback.format_exception(exception))
                container.logging.error(traceback_str)
                raise RuntimeError("Error including router") from exception
            yield
        except Exception as exception:
            container.logging.error(f"Error in lifespan: {exception}")
            traceback_str: str = "".join(traceback.format_exception(exception))
            container.logging.error(traceback_str)
            raise RuntimeError("Error in lifespan") from exception
        finally:
            container.logging.info("Container shut down")
            await container.stop()


def create_application() -> FastAPI:
    container = AgentContainer()
    application = FastAPI(title="agent", lifespan=lambda app: _lifespan(app, container))

    application.add_middleware(RequestIDMiddleware)
    application.add_middleware(RequestMiddleware)
    # noinspection PyTypeChecker
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.mount("/mcp", container.mcp_asgi_app)

    return application
