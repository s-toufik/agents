import traceback
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, APIRouter
from starlette.middleware.cors import CORSMiddleware

from agentic_application.bootstrap.container.agent.agent_container import AgentContainer
from agentic_application.bootstrap.container.container import Container
from agentic_core.infrastructure.http.middleware.request_id_middleware import RequestIDMiddleware
from agentic_core.infrastructure.http.middleware.request_middleware import RequestMiddleware


@asynccontextmanager
async def _lifespan(application: FastAPI) -> AsyncGenerator[None, None]:
    container: Container = AgentContainer()
    status: bool
    exception: Exception
    status, exception = await container.boot
    container.logging.info("Container booted")
    if not status and exception:
        container.logging.error(f"Container failed to boot: {exception}")
        traceback_str: str = "".join(traceback.format_exception(exception))
        container.logging.error(traceback_str)
        raise RuntimeError("Container failed to boot") from exception

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
    application = FastAPI(title="agent", lifespan=lambda app: _lifespan(app))

    application.add_middleware(RequestIDMiddleware)
    application.add_middleware(RequestMiddleware)
    # noinspection PyTypeChecker
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return application
