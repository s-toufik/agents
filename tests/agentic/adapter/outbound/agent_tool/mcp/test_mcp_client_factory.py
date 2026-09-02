import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from pycraftcore.application_configuration.enum.connector_type import ConnectorType
from pycraftcore.application_configuration.model.connector import McpConnector
from pycraftcore.authentication.model.auth_type import AuthType
from pycraftcore.authentication.model.basic_auth import BasicAuth
from pycraftcore.authentication.model.no_auth import NoAuth
from pycraftcore.authentication.model.token_auth import TokenAuth

from agentic.adapter.outbound.agent_tool.mcp.mcp_client_factory import McpClientFactory

_MODULE = "agentic.adapter.outbound.agent_tool.mcp.mcp_client_factory"


class FakeAsyncContextManager:
    def __init__(self, enter_value=None):
        self.enter_value = enter_value
        self.entered = False
        self.exited = False

    async def __aenter__(self):
        self.entered = True
        return self.enter_value

    async def __aexit__(self, *exc_info):
        self.exited = True
        return False


def make_connector(transport="streamable_http", auth=None):
    return McpConnector(
        name="tools",
        type=ConnectorType.mcp,
        auth=auth or NoAuth(type=AuthType.none),
        base_url="https://mcp.test.com",
        timeout=5,
        transport=transport,
    )


def make_session():
    session = MagicMock()
    session.initialize = AsyncMock()
    return session


@pytest.mark.asyncio
async def test_start_over_streamable_http_wires_the_client_into_the_transport():
    connector = make_connector(transport="streamable_http")
    fake_http_client = FakeAsyncContextManager()
    fake_transport = FakeAsyncContextManager(enter_value=("read", "write"))
    session = make_session()

    with (
        patch(f"{_MODULE}.create_mcp_http_client", return_value=fake_http_client),
        patch(f"{_MODULE}.streamable_http_client", return_value=fake_transport) as mock_transport,
        patch(f"{_MODULE}.ClientSession", return_value=FakeAsyncContextManager(session)) as mock_session_cls,
    ):
        factory = McpClientFactory(connector)
        await factory.start()

    mock_transport.assert_called_once_with(connector.base_url, http_client=fake_http_client)
    mock_session_cls.assert_called_once_with("read", "write")
    assert fake_http_client.entered is True
    session.initialize.assert_awaited_once()
    assert factory.create_client() is session


@pytest.mark.asyncio
async def test_start_over_sse_passes_headers_and_timeout_directly():
    connector = make_connector(transport="sse", auth=TokenAuth(key_name="X-Api-Key", key_value="secret"))
    fake_transport = FakeAsyncContextManager(enter_value=("read", "write"))
    session = make_session()

    with (
        patch(f"{_MODULE}.sse_client", return_value=fake_transport) as mock_sse,
        patch(f"{_MODULE}.ClientSession", return_value=FakeAsyncContextManager(session)),
    ):
        factory = McpClientFactory(connector)
        await factory.start()

    mock_sse.assert_called_once_with(
        connector.base_url, headers={"X-Api-Key": "secret"}, timeout=5
    )
    assert factory.create_client() is session


@pytest.mark.asyncio
async def test_start_is_idempotent():
    connector = make_connector(transport="sse")
    fake_transport = FakeAsyncContextManager(enter_value=("read", "write"))
    session = make_session()

    with (
        patch(f"{_MODULE}.sse_client", return_value=fake_transport),
        patch(f"{_MODULE}.ClientSession", return_value=FakeAsyncContextManager(session)),
    ):
        factory = McpClientFactory(connector)
        await factory.start()
        await factory.start()

    session.initialize.assert_awaited_once()


def test_create_client_raises_before_start():
    factory = McpClientFactory(make_connector())

    with pytest.raises(RuntimeError):
        factory.create_client()


@pytest.mark.asyncio
async def test_close_tears_down_the_stack_and_allows_a_fresh_start():
    connector = make_connector(transport="sse")
    fake_transport = FakeAsyncContextManager(enter_value=("read", "write"))
    session_cm = FakeAsyncContextManager(make_session())

    with (
        patch(f"{_MODULE}.sse_client", return_value=fake_transport),
        patch(f"{_MODULE}.ClientSession", return_value=session_cm),
    ):
        factory = McpClientFactory(connector)
        await factory.start()
        await factory.close()

    assert fake_transport.exited is True
    assert session_cm.exited is True
    with pytest.raises(RuntimeError):
        factory.create_client()


@pytest.mark.asyncio
async def test_close_before_start_is_a_no_op():
    factory = McpClientFactory(make_connector())

    await factory.close()  # must not raise


@pytest.mark.asyncio
async def test_start_failure_tears_down_whatever_was_already_entered():
    # If session.initialize() blows up, the already-opened transport must not leak.
    connector = make_connector(transport="sse")
    fake_transport = FakeAsyncContextManager(enter_value=("read", "write"))
    session = MagicMock()
    session.initialize = AsyncMock(side_effect=ConnectionError("handshake failed"))

    with (
        patch(f"{_MODULE}.sse_client", return_value=fake_transport),
        patch(f"{_MODULE}.ClientSession", return_value=FakeAsyncContextManager(session)),
    ):
        factory = McpClientFactory(connector)
        with pytest.raises(ConnectionError):
            await factory.start()

    assert fake_transport.exited is True
    with pytest.raises(RuntimeError):
        factory.create_client()


def test_token_auth_produces_a_single_header():
    connector = make_connector(auth=TokenAuth(key_name="X-Api-Key", key_value="secret"))

    assert McpClientFactory(connector)._headers() == {"X-Api-Key": "secret"}


def test_basic_auth_produces_a_basic_authorization_header():
    connector = make_connector(auth=BasicAuth(username="user", password="pass"))

    headers = McpClientFactory(connector)._headers()

    assert headers["Authorization"].startswith("Basic ")


def test_no_auth_produces_no_headers():
    connector = make_connector(auth=NoAuth(type=AuthType.none))

    assert McpClientFactory(connector)._headers() == {}
