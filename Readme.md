# agent

## Setup

```bash
uv sync --group dev
```

## Development

```bash
make test      # run the unit test suite (uv run pytest)
make lint       # ruff check
make format     # ruff format
make typing     # mypy --strict
```

## MCP

The agent hosts its own [MCP](https://modelcontextprotocol.io) server and can also consume tools from an external one. Both paths use the `mcp` Python SDK.

### Self-hosted MCP server

The app mounts its own MCP server at `/mcp` (see `create_application.py`), exposing the agent's native tools:

- `users_tables` — SQL query tool over the users database
- `python_executor` — sandboxed Python execution

This starts automatically with the app — no extra config needed. The agent's own `ToolRegistry` is built by connecting to this same server in-process (no HTTP round trip), so whatever the MCP endpoint serves is exactly what the agent itself uses.

#### Connecting external clients (e.g. Claude Desktop)

`/mcp` speaks streamable-HTTP and can be reached by any MCP client, not just the agent itself.

1. **Run the app**, e.g. `uvicorn agentic_application.application.agent.create_application:app --host 0.0.0.0 --port 8000`. `0.0.0.0` here just means "listen on every interface" — it is never a valid *client* URL, only a bind address.

2. **Get an HTTPS URL in front of it.** Claude Desktop's custom-connector field requires `https` — there is no plain-`http` exception, not even for `localhost`. If you have [Tailscale](https://tailscale.com) running on the machine (recommended — stays private to your tailnet, no public exposure):

   ```bash
   tailscale serve --bg 8000
   tailscale serve status   # prints the assigned https://<machine-name>.<tailnet-name>.ts.net URL
   ```

   That proxies the whole port over HTTPS on your tailnet, including `/mcp`, using a cert issued via Tailscale's MagicDNS. (If it refuses to start, enable *DNS → HTTPS Certificates* for the tailnet in the Tailscale admin console first.) Without Tailscale, a tunnel works the same way — `ngrok http 8000` or `cloudflared tunnel --url http://localhost:8000`. For a real deployment, use its actual HTTPS URL instead.

3. **Configure allowed hosts.** MCP's DNS-rebinding protection denies every host by default (`allowed_hosts=[]`), so any external request — including through Tailscale — currently gets `421 Invalid Host header`. Add the host you'll actually be reached at in `AgentContainer.mcp_asgi_app`:

   ```python
   # agent_container.py
   from mcp.server.transport_security import TransportSecuritySettings

   @cached_property
   def mcp_asgi_app(self) -> Starlette:
       return self._mcp_server.streamable_http_app(
           streamable_http_path="/",
           transport_security=TransportSecuritySettings(allowed_hosts=["<machine-name>.<tailnet-name>.ts.net"]),
       )
   ```

4. **Point Claude Desktop at it.** This is a remote HTTP server, not a locally-spawned stdio one, so it's added as a custom connector rather than through `claude_desktop_config.json`: in Claude Desktop go to *Settings → Connectors → Add custom connector* and enter the HTTPS URL from step 2 (`https://<machine-name>.<tailnet-name>.ts.net/mcp`). Claude Desktop can then call `users_tables` and `python_executor` directly.

### External MCP (connecting out to another server)

`McpClientFactory` (`agentic/adapter/outbound/agent_tool/mcp/mcp_client_factory.py`) lets the agent consume tools from a *remote* MCP server, the same way `McpInProcessClientFactory` does for the self-hosted one.

Configure it as an `mcp` connector, e.g. `config/debug/connector/mcp.yml`:

```yaml
connector:
  tools:
    name: mcp_tools
    type: mcp
    base_url: http://localhost:8000/mcp
    timeout: 5
    transport: streamable_http   # or "sse"
    certificate: ""
    auth:
      type: none                 # or token / basic
```

...and reference it from `config/root.yml`:

```yaml
connector:
  mcp:
    tools: ${connector.tools}
```

`AgentDI._mcp_client_factory` reads this connector and builds the client — it's already wired up as a `cached_property` with close-on-shutdown, but it isn't merged into the agent's active `ToolRegistry` today (`_tool_registry()` only pulls tools from the self-hosted, in-process server). To make the agent actually use tools from an external server, merge them in the same way, e.g.:

```python
async def _tool_registry(self) -> ToolRegistry:
    await self._mcp_in_process_client_factory.start()
    await self._mcp_client_factory.start()

    tools = await McpToolProvider(self._mcp_in_process_client_factory).tools()
    tools += await McpToolProvider(self._mcp_client_factory).tools()

    return ToolRegistry(tools=tools)
```

Don't forget to also close it in `AgentContainer.stop()` — `_close_mcp_client_factory()` is already there, just currently unused because nothing calls `.start()` on it yet.

## Pre-commit hooks

This repo uses [pre-commit](https://pre-commit.com) to run the unit test suite before every commit and push (see `.pre-commit-config.yaml`). Git hooks live under `.git/hooks/` and aren't tracked by git, so after cloning or pulling this change, install them once:

```bash
uv run pre-commit install --hook-type pre-commit --hook-type pre-push
```

After that, `git commit` and `git push` will run `uv run pytest` automatically and abort on failure. To run the hooks manually against the whole repo:

```bash
uv run pre-commit run --all-files --hook-stage pre-commit
```
