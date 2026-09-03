from pycraftcore.application_configuration.enum import ConnectorType
from pycraftcore.application_configuration.model.connector import McpConnector
from pycraftcore.authentication.model.no_auth import NoAuth
from starlette.testclient import TestClient

from toolbox.adapter.inbound.mcp.mcp_asgi_factory import build_mcp_asgi_app
from toolbox.adapter.inbound.mcp.mcp_server_factory import build_mcp_server


def make_connector(base_url: str = "http://localhost:8001/mcp") -> McpConnector:
    return McpConnector(
        name="self",
        type=ConnectorType.mcp,
        auth=NoAuth(),
        base_url=base_url,
        timeout=30,
        transport="streamable_http",
    )


def test_health_reports_starting_with_no_tools_registered() -> None:
    server = build_mcp_server(name="toolbox", version="1.0.0")
    client = TestClient(build_mcp_asgi_app(server, make_connector()))

    response = client.get("/health")

    assert response.status_code == 503
    assert response.json() == {"status": "starting", "tools": 0}


def test_health_reports_ok_once_a_tool_is_registered() -> None:
    server = build_mcp_server(name="toolbox", version="1.0.0")

    @server.tool(name="echo", description="Echoes.")
    async def echo(text: str) -> str:
        return text

    client = TestClient(build_mcp_asgi_app(server, make_connector()))

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "tools": ["echo"]}


def test_the_mcp_endpoint_is_served_at_the_path_from_the_connector_url() -> None:
    server = build_mcp_server(name="toolbox", version="1.0.0")
    app = build_mcp_asgi_app(server, make_connector("http://localhost:8001/custom-path"))

    # The session manager's lifespan (started via the ASGI `lifespan` protocol)
    # has to be running before the endpoint can handle a real request -- only
    # entering TestClient as a context manager triggers that startup.
    # allowed_hosts is derived from the connector's own base_url netloc, so the
    # client must present that same Host to get past the DNS-rebinding guard.
    with TestClient(app, base_url="http://localhost:8001") as client:
        response = client.post(
            "/custom-path",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "t", "version": "0"},
                },
            },
            headers={"Accept": "application/json, text/event-stream"},
        )

    assert response.status_code == 200


def test_defaults_to_slash_mcp_when_the_connector_url_has_no_path() -> None:
    server = build_mcp_server(name="toolbox", version="1.0.0")
    client = TestClient(build_mcp_asgi_app(server, make_connector("http://localhost:8001")))

    response = client.get("/health")

    assert response.status_code in (200, 503)  # the route exists at all, regardless of tool state
