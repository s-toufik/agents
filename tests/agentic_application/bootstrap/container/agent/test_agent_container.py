from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp.server.mcpserver import MCPServer

from agentic_application.bootstrap.container.agent.agent_container import AgentContainer


def make_container() -> AgentContainer:
    container = AgentContainer()
    container.__dict__["_llm_httpx_factory"] = MagicMock()
    return container


@pytest.mark.asyncio
async def test_boot_does_not_start_the_external_mcp_client():

    container = make_container()
    mcp_client_factory = MagicMock()
    mcp_client_factory.start = AsyncMock()
    container.__dict__["_mcp_client_factory"] = mcp_client_factory

    with (
        patch.object(AgentContainer, "_switch_factories", AsyncMock()),
        patch.object(AgentContainer, "_register_mcp_tools", AsyncMock()) as mock_register,
    ):
        status, exception = await container.boot

    assert status is True
    assert exception is None
    mcp_client_factory.start.assert_not_called()
    mock_register.assert_awaited_once()


@pytest.mark.asyncio
async def test_boot_registers_mcp_tools():
    container = make_container()

    with (
        patch.object(AgentContainer, "_switch_factories", AsyncMock()),
        patch.object(AgentContainer, "_register_mcp_tools", AsyncMock()) as mock_register,
    ):
        await container.boot

    mock_register.assert_awaited_once()


@pytest.mark.asyncio
async def test_boot_failure_is_caught_and_reported_not_raised():
    container = make_container()

    with patch.object(
        AgentContainer, "_switch_factories", AsyncMock(side_effect=RuntimeError("boom"))
    ):
        status, exception = await container.boot

    assert status is False
    assert isinstance(exception, RuntimeError)


@pytest.mark.asyncio
async def test_stop_closes_both_the_external_and_in_process_mcp_factories():
    container = make_container()

    with (
        patch.object(AgentContainer, "_switch_factories", AsyncMock()),
        patch.object(AgentContainer, "_close_llm_http_client", AsyncMock()),
        patch.object(AgentContainer, "_shutdown_telemetry", AsyncMock()),
        patch.object(AgentContainer, "_close_mcp_client_factory", AsyncMock()) as close_external,
        patch.object(
            AgentContainer, "_close_mcp_in_process_client_factory", AsyncMock()
        ) as close_in_process,
    ):
        await container.stop()

    close_external.assert_awaited_once()
    close_in_process.assert_awaited_once()


@pytest.mark.asyncio
async def test_mcp_lifespan_enters_and_exits_the_real_session_manager_cleanly():
    container = make_container()
    container.__dict__["_mcp_server"] = MCPServer(name="test")

    async with container.mcp_lifespan():
        pass  # must not raise
